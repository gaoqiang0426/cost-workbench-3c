import streamlit as st

from cost_workbench.cost_engine import (
    MACHINE_RATES_YUAN_PER_SECOND,
    SURFACE_TREATMENT_RATES_YUAN_PER_CM2,
    breakdown_rows,
    estimate_process_cost,
)
from cost_workbench.input_analysis import analyze_images, analyze_step_file
from cost_workbench.material_library import get_material, material_names_for_process
from cost_workbench.optimization import generate_optimization_suggestions
from cost_workbench.process_parameters import summarize_process_parameters
from cost_workbench.process_routes import get_process_route
from cost_workbench.report_generator import build_report, generate_pdf_report


st.set_page_config(
    page_title="3C 结构件成本估算工作台",
    page_icon="¥",
    layout="wide",
)


PROCESS_OPTIONS = ["注塑件", "CNC铝件", "铝合金冲压", "钣金件", "锌合金压铸", "3D打印"]


def main() -> None:
    _init_state()
    _inject_styles()
    _render_header()

    if st.session_state.page == 1:
        _page_input_analysis()
    elif st.session_state.page == 2:
        _page_route_and_cost()
    else:
        _page_optimization()


def _init_state() -> None:
    st.session_state.setdefault("page", 1)
    st.session_state.setdefault("analysis", None)
    st.session_state.setdefault("cost_result", None)
    st.session_state.setdefault("route", None)
    st.session_state.setdefault("suggestions", None)


def _render_header() -> None:
    st.markdown(
        """
        <section class="hero-band">
          <div>
            <h1>3C 结构件成本预评估工作台</h1>
            <p>输入文件与工程参数，自动生成工艺路线、成本拆解和结构优化建议。</p>
          </div>
        </section>
        """,
        unsafe_allow_html=True,
    )
    steps = ["1 输入分析", "2 路线与成本", "3 优化建议"]
    st.progress((st.session_state.page - 1) / 2)
    st.write(" / ".join(f"**{step}**" if i + 1 == st.session_state.page else step for i, step in enumerate(steps)))


def _inject_styles() -> None:
    st.markdown(
        """
        <style>
        .block-container { padding-top: 2rem; max-width: 1240px; }
        .hero-band {
            border: 1px solid #d9e2ec;
            border-radius: 8px;
            padding: 22px 26px;
            margin-bottom: 18px;
            background: #f8fafc;
        }
        .hero-band h1 {
            margin: 0;
            font-size: 34px;
            line-height: 1.2;
            letter-spacing: 0;
            color: #1f2937;
        }
        .hero-band p {
            margin: 8px 0 0;
            color: #64748b;
            font-size: 15px;
        }
        div[data-testid="stMetric"] {
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            padding: 12px 14px;
            background: #ffffff;
        }
        div[data-testid="stExpander"] {
            border-radius: 8px;
            border-color: #d9e2ec;
        }
        .stButton > button, .stDownloadButton > button {
            border-radius: 6px;
            font-weight: 650;
        }
        .route-node {
            border: 1px solid #d9e2ec;
            border-radius: 8px;
            padding: 12px 14px;
            margin: 8px 0;
            background: #ffffff;
        }
        .route-index {
            width: 34px;
            height: 34px;
            border-radius: 50%;
            background: #e0f2fe;
            color: #0369a1;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            font-weight: 700;
            margin-right: 10px;
        }
        .route-title { font-weight: 750; color: #111827; }
        .route-meta {
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: 8px;
            margin-top: 8px;
            font-size: 13px;
            color: #4b5563;
        }
        @media (max-width: 760px) {
            .route-meta { grid-template-columns: 1fr; }
            .hero-band h1 { font-size: 28px; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _page_input_analysis() -> None:
    left, right = st.columns([0.95, 1.05], gap="large")

    with left:
        st.subheader("输入方式")
        input_method = st.radio(
            "选择一种输入方式",
            ["STEP 文件", "Creo 截图"],
            horizontal=True,
            help="两种方式任选其一。STEP 用于后续几何解析；截图用于视图识别和局部优化标注。",
        )

        step_result = None
        image_result = None
        if input_method == "STEP 文件":
            step_file = st.file_uploader("拖入或选择 .stp/.step 文件", type=["stp", "step"])
            if step_file is not None:
                step_result = analyze_step_file(step_file.name, step_file.getvalue())
                st.dataframe(
                    [{"字段": key, "结果": value} for key, value in step_result.items()],
                    use_container_width=True,
                    hide_index=True,
                )
            else:
                st.info("将 STEP 文件拖入此处，后续会接入真实体积、包围盒和表面积分析。")
        else:
            st.markdown("截图可本地拖入上传；复制粘贴图片在 Streamlit 原生模式下需要浏览器组件增强，当前先保留粘贴区说明和上传入口。")
            image_files = st.file_uploader(
                "拖入或选择 Creo 截图",
                type=["png", "jpg", "jpeg", "bmp", "webp"],
                accept_multiple_files=True,
            )
            paste_note = st.text_area(
                "截图粘贴说明/备注",
                placeholder="可在这里记录截图来源、视图说明或复制粘贴失败时的补充说明。",
                height=88,
            )
            if image_files:
                image_result = analyze_images(
                    [{"name": item.name, "size": len(item.getvalue())} for item in image_files]
                )
                st.dataframe(image_result["items"], use_container_width=True, hide_index=True)
                preview_cols = st.columns(min(3, len(image_files)))
                for index, item in enumerate(image_files[:6]):
                    with preview_cols[index % len(preview_cols)]:
                        st.image(item, caption=item.name, use_container_width=True)
                if not image_result["is_enough_for_report"]:
                    st.warning("少于 3 张截图，后续报告会标记为草稿分析。")
            elif paste_note:
                image_result = {
                    "count": 0,
                    "is_enough_for_report": False,
                    "items": [],
                    "message": paste_note,
                }

    with right:
        st.subheader("自动分析与参数确认")
        part_name = st.text_input("零件名称", value=_default_part_name(input_method, step_result))
        process = st.selectbox("推荐/选择工艺路线", PROCESS_OPTIONS)

        material_options = material_names_for_process(process)
        material_name = st.selectbox("材料选型", material_options)
        material = get_material(material_name)
        geometry_defaults = _geometry_defaults(step_result, material, process)

        info_a, info_b, info_c = st.columns(3)
        info_a.metric("材料密度", f"{material['density_g_cm3']} g/cm³")
        info_b.metric("参考单价", f"{material['price_yuan_kg']} 元/kg")
        info_c.metric("材料类别", material["category"])

        weight_col, price_col = st.columns(2)
        with weight_col:
            weight_value = st.number_input("材料/产品克重", min_value=0.01, value=geometry_defaults["weight_g"], step=1.0)
            weight_unit = st.selectbox("重量单位", ["g", "kg"], index=0)
        with price_col:
            material_price = st.number_input("材料单价", min_value=0.0, value=float(material["price_yuan_kg"]), step=1.0)
            price_unit = st.selectbox("单价单位", ["元/kg", "元/g"], index=0)

        dim_a, dim_b, dim_c = st.columns(3)
        length = dim_a.number_input("长", min_value=0.0, value=geometry_defaults["length_mm"], step=1.0)
        width = dim_b.number_input("宽", min_value=0.0, value=geometry_defaults["width_mm"], step=1.0)
        height = dim_c.number_input("高", min_value=0.0, value=geometry_defaults["height_mm"], step=1.0)
        dimension_unit = st.selectbox("尺寸单位", ["mm", "cm"], index=0)

        process_a, process_b, process_c = st.columns(3)
        batch_qty = process_a.number_input("批量", min_value=1, value=1000, step=100)
        complexity = process_b.selectbox("结构复杂度", ["低", "中", "高"], index=1)
        surface_treatment = process_c.selectbox("表面处理", list(SURFACE_TREATMENT_RATES_YUAN_PER_CM2.keys()))

        surface_area = st.number_input("外表面积估算", min_value=0.0, value=geometry_defaults["surface_area_cm2"], step=5.0)
        surface_area_unit = st.selectbox("面积单位", ["cm²", "mm²"], index=0)

        process_parameter_values = _render_process_parameter_inputs(process)
        process_parameter_summary = summarize_process_parameters(process, process_parameter_values)

        with st.expander("材料工程说明", expanded=True):
            st.write(f"- 强度：{material['strength']}")
            st.write(f"- 重量：{material['weight']}")
            st.write(f"- 成本：{material['cost']}")
            st.write(f"- 表面处理：{material['surface']}")
            st.write(f"- 制造风险：{material['risk']}")

        analysis = {
            "input_method": input_method,
            "part_name": part_name,
            "process": process,
            "material_name": material_name,
            "material": material,
            "weight_g": _to_g(weight_value, weight_unit),
            "material_price_yuan_kg": _to_yuan_kg(material_price, price_unit),
            "length_mm": _to_mm(length, dimension_unit),
            "width_mm": _to_mm(width, dimension_unit),
            "height_mm": _to_mm(height, dimension_unit),
            "batch_qty": int(batch_qty),
            "complexity": complexity,
            "surface_treatment": surface_treatment,
            "surface_area_cm2": _to_cm2(surface_area, surface_area_unit),
            "injection_cycle_s": _to_seconds(
                process_parameter_values.get("injection_cycle_s", 30.0),
                process_parameter_values.get("cycle_unit", "s"),
            ),
            "machine_tonnage": process_parameter_values.get("machine_tonnage", "120T"),
            "cavities": int(process_parameter_values.get("cavities", 1)),
            "defect_rate": process_parameter_values.get("defect_rate_percent", 3.0) / 100,
            "defect_rate_percent": process_parameter_values.get("defect_rate_percent", 3.0),
            "mold_amortization_per_piece": process_parameter_values.get("mold_amortization_per_piece", 0.0),
            "process_parameter_values": process_parameter_values,
            "process_parameter_summary": process_parameter_summary,
            "step_result": step_result,
            "image_result": image_result,
        }

        st.markdown("**自动分析摘要**")
        st.dataframe(_analysis_rows(analysis), use_container_width=True, hide_index=True)

        if st.button("下一步：生成工艺路线与成本", type="primary", use_container_width=True):
            st.session_state.analysis = analysis
            st.session_state.page = 2
            st.rerun()


def _page_route_and_cost() -> None:
    analysis = st.session_state.analysis
    if not analysis:
        st.warning("请先完成第一页输入。")
        if st.button("返回输入页"):
            st.session_state.page = 1
            st.rerun()
        return

    cost_result = estimate_process_cost(
        process=analysis["process"],
        product_weight_g=analysis["weight_g"],
        material_price_per_kg=analysis["material_price_yuan_kg"],
        batch_qty=analysis["batch_qty"],
        complexity=analysis["complexity"],
        surface_treatment=analysis["surface_treatment"],
        surface_area_cm2=analysis["surface_area_cm2"],
        supplier_margin_rate=0.15,
        injection_cycle_s=analysis["injection_cycle_s"],
        machine_tonnage=analysis["machine_tonnage"],
        cavities=analysis["cavities"],
        defect_rate=analysis["defect_rate"],
        mold_amortization_per_piece=analysis["mold_amortization_per_piece"],
        process_fee_multiplier=analysis["process_parameter_summary"]["process_fee_multiplier"],
        extra_process_fee=analysis["process_parameter_summary"]["extra_process_fee"],
    )
    route = get_process_route(analysis["process"])
    st.session_state.cost_result = cost_result
    st.session_state.route = route

    left, right = st.columns([1.08, 0.92], gap="large")
    with left:
        st.subheader("自动计算工艺路线图")
        _render_route(route)

    with right:
        st.subheader("成本拆解值")
        st.metric("最终单件预估价", f"{cost_result['unit_price']:.2f} 元/件")
        st.dataframe(breakdown_rows(cost_result), use_container_width=True, hide_index=True)
        with st.expander("成本判断", expanded=True):
            for item in analysis.get("process_parameter_summary", {}).get("summary", []):
                st.write(f"- {item}")
            for note in cost_result["notes"]:
                st.write(f"- {note}")

    nav_a, nav_b = st.columns(2)
    if nav_a.button("上一步：修改输入", use_container_width=True):
        st.session_state.page = 1
        st.rerun()
    if nav_b.button("下一页：生成优化建议", type="primary", use_container_width=True):
        st.session_state.suggestions = generate_optimization_suggestions(
            analysis["process"],
            analysis["material"],
            analysis,
            cost_result,
        )
        st.session_state.page = 3
        st.rerun()


def _page_optimization() -> None:
    analysis = st.session_state.analysis
    cost_result = st.session_state.cost_result
    route = st.session_state.route or []
    suggestions = st.session_state.suggestions
    if not analysis or not cost_result:
        st.warning("请先完成前两页分析。")
        if st.button("返回输入页"):
            st.session_state.page = 1
            st.rerun()
        return

    if suggestions is None:
        suggestions = generate_optimization_suggestions(
            analysis["process"],
            analysis["material"],
            analysis,
            cost_result,
        )
        st.session_state.suggestions = suggestions

    st.subheader("结合实际输入的优化建议")
    left, right = st.columns([1, 1], gap="large")

    with left:
        st.markdown("**分析依据**")
        st.dataframe(_analysis_rows(analysis), use_container_width=True, hide_index=True)
        st.markdown("**主要成本项**")
        st.dataframe(breakdown_rows(cost_result), use_container_width=True, hide_index=True)

    with right:
        for group_name, items in suggestions.items():
            st.markdown(f"**{group_name}**")
            for item in items:
                st.markdown(
                    f"""
                    <div style="border:1px solid #e5e7eb;border-radius:8px;padding:12px;margin:8px 0;background:#fff">
                      <div style="font-weight:700">{item['编号']}：{item['建议动作']}</div>
                      <div style="margin-top:4px;color:#374151">原因：{item['工程原因']}</div>
                      <div style="margin-top:4px;color:#0f766e">影响：{item['影响']}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

    report = build_report(
        part_name=analysis["part_name"],
        process=analysis["process"],
        cost_result=cost_result,
        route_steps=route,
        suggestions=suggestions,
        inputs={
            "输入方式": analysis["input_method"],
            "材料选型": analysis["material_name"],
            "重量(g)": round(analysis["weight_g"], 2),
            "材料单价(元/kg)": round(analysis["material_price_yuan_kg"], 2),
            "长宽高(mm)": f"{analysis['length_mm']} x {analysis['width_mm']} x {analysis['height_mm']}",
            "批量(pcs)": analysis["batch_qty"],
            "结构复杂度": analysis["complexity"],
            "表面处理": analysis["surface_treatment"],
            "外表面积(cm²)": round(analysis["surface_area_cm2"], 2),
            "STEP文件": analysis["step_result"]["file_name"] if analysis["step_result"] else "未上传",
            "截图数量": analysis["image_result"]["count"] if analysis["image_result"] else 0,
            "加工参数": "；".join(analysis.get("process_parameter_summary", {}).get("summary", [])),
        },
    )
    pdf_bytes = generate_pdf_report(report)

    nav_a, nav_b, nav_c = st.columns(3)
    if nav_a.button("返回第一页", use_container_width=True):
        st.session_state.page = 1
        st.rerun()
    if nav_b.button("返回第二页", use_container_width=True):
        st.session_state.page = 2
        st.rerun()
    nav_c.download_button(
        "下载 PDF 报告",
        data=pdf_bytes,
        file_name=f"{analysis['part_name']}_成本预估报告.pdf",
        mime="application/pdf",
        use_container_width=True,
    )


def _render_route(route: list[dict[str, str]]) -> None:
    for index, step in enumerate(route, start=1):
        st.markdown(
            f"""
            <div style="border:1px solid #e5e7eb;border-radius:8px;padding:12px 14px;margin:8px 0;background:#ffffff">
              <div style="display:flex;align-items:center;gap:10px">
                <div style="width:34px;height:34px;border-radius:50%;background:#eff6ff;color:#1d4ed8;display:flex;align-items:center;justify-content:center;font-weight:700">{index}</div>
                <div style="font-weight:700;color:#111827">{step['name']}</div>
              </div>
              <div style="color:#374151;margin-top:8px">{step['description']}</div>
              <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:8px;margin-top:8px;font-size:13px;color:#4b5563">
                <div><b>风险：</b>{step['risk']}</div>
                <div><b>成本项：</b>{step['cost_item']}</div>
                <div><b>几何依据：</b>{step['geometry_basis']}</div>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def _render_process_parameter_inputs(process: str) -> dict:
    st.markdown("**加工机台参数**")
    if process == "注塑件":
        inj_a, inj_b, inj_c = st.columns(3)
        injection_cycle_s = inj_a.number_input("注塑周期", min_value=0.1, value=30.0, step=1.0)
        cycle_unit = inj_a.selectbox("周期单位", ["s", "min"], index=0)
        machine_tonnage = inj_b.selectbox("注塑机吨位", list(MACHINE_RATES_YUAN_PER_SECOND.keys()), index=1)
        cavities = inj_c.number_input("一模出数", min_value=1, value=2, step=1)
        defect_rate_percent = st.number_input("不良率 (%)", min_value=0.0, max_value=95.0, value=5.0, step=0.5)
        mold_amortization = st.number_input("模具费摊销 (元/件)", min_value=0.0, value=0.8, step=0.1)
        return {
            "injection_cycle_s": injection_cycle_s,
            "cycle_unit": cycle_unit,
            "machine_tonnage": machine_tonnage,
            "cavities": int(cavities),
            "defect_rate_percent": defect_rate_percent,
            "mold_amortization_per_piece": mold_amortization,
        }

    if process == "CNC铝件":
        col_a, col_b, col_c = st.columns(3)
        return {
            "cnc_machine": col_a.selectbox("CNC机台", ["3轴CNC", "4轴CNC", "5轴CNC"]),
            "setup_count": col_b.number_input("装夹次数", min_value=1, value=2, step=1),
            "machining_time_min": col_c.number_input("单件机加工时间(min)", min_value=1.0, value=30.0, step=1.0),
        }

    if process == "铝合金冲压":
        col_a, col_b, col_c = st.columns(3)
        return {
            "press_tonnage": col_a.selectbox("冲床吨位", ["45T", "80T", "110T", "160T"], index=1),
            "station_count": col_b.number_input("工站数", min_value=1, value=5, step=1),
            "die_amortization_per_piece": col_c.number_input("冲压模具摊销(元/件)", min_value=0.0, value=0.35, step=0.05),
        }

    if process == "钣金件":
        col_a, col_b, col_c = st.columns(3)
        return {
            "cutting_method": col_a.selectbox("开料方式", ["激光切割", "数冲", "模具冲裁"]),
            "bend_count": col_b.number_input("折弯次数", min_value=0, value=4, step=1),
            "rivet_count": col_c.number_input("压铆数量", min_value=0, value=2, step=1),
        }

    if process == "锌合金压铸":
        col_a, col_b, col_c = st.columns(3)
        die_cast_machine = col_a.selectbox("压铸机吨位", ["88T", "160T", "280T"], index=1)
        die_cast_cycle_s = col_b.number_input("压铸周期(s)", min_value=1.0, value=35.0, step=1.0)
        die_cast_cavities = col_c.number_input("一模出数", min_value=1, value=2, step=1)
        die_cast_mold_amortization = st.number_input("压铸模具摊销(元/件)", min_value=0.0, value=0.6, step=0.1)
        return {
            "die_cast_machine": die_cast_machine,
            "die_cast_cycle_s": die_cast_cycle_s,
            "die_cast_cavities": int(die_cast_cavities),
            "die_cast_mold_amortization": die_cast_mold_amortization,
        }

    col_a, col_b, col_c = st.columns(3)
    return {
        "print_technology": col_a.selectbox("打印工艺", ["SLA", "SLS", "FDM", "MJF"]),
        "print_time_h": col_b.number_input("打印时间(h)", min_value=0.1, value=6.0, step=0.5),
        "post_process": col_c.selectbox("后处理", ["基础去支撑", "打磨喷漆", "精修外观"]),
    }


def _analysis_rows(analysis: dict) -> list[dict[str, object]]:
    rows = [
        ("输入方式", analysis["input_method"]),
        ("工艺路线", analysis["process"]),
        ("材料", analysis["material_name"]),
        ("重量", f"{analysis['weight_g']:.2f} g"),
        ("材料单价", f"{analysis['material_price_yuan_kg']:.2f} 元/kg"),
        ("尺寸", f"{analysis['length_mm']:.1f} x {analysis['width_mm']:.1f} x {analysis['height_mm']:.1f} mm"),
        ("批量", f"{analysis['batch_qty']} pcs"),
        ("复杂度", analysis["complexity"]),
        ("表面处理", analysis["surface_treatment"]),
        ("外表面积", f"{analysis['surface_area_cm2']:.1f} cm²"),
    ]
    for item in analysis.get("process_parameter_summary", {}).get("summary", []):
        rows.append(("加工参数", item))
    if analysis["step_result"]:
        rows.append(("STEP", f"{analysis['step_result']['file_name']} / {analysis['step_result']['schema']}"))
    if analysis["image_result"]:
        rows.append(("截图数量", analysis["image_result"]["count"]))
    return [{"项目": key, "分析值": value} for key, value in rows]


def _default_part_name(input_method: str, step_result: dict | None) -> str:
    if step_result:
        return step_result["file_name"].rsplit(".", 1)[0]
    return "3C结构件" if input_method == "STEP 文件" else "Creo截图分析件"


def _default_weight(process: str) -> float:
    defaults = {
        "注塑件": 50.0,
        "CNC铝件": 80.0,
        "铝合金冲压": 35.0,
        "钣金件": 60.0,
        "锌合金压铸": 95.0,
        "3D打印": 45.0,
    }
    return defaults.get(process, 50.0)


def _geometry_defaults(
    step_result: dict | None,
    material: dict,
    process: str,
) -> dict[str, float]:
    defaults = {
        "weight_g": _default_weight(process),
        "length_mm": 80.0,
        "width_mm": 40.0,
        "height_mm": 12.0,
        "surface_area_cm2": 120.0,
    }
    if not step_result or step_result.get("status") != "解析成功":
        return defaults

    volume_mm3 = step_result.get("volumeMm3")
    surface_area_mm2 = step_result.get("outerSurfaceAreaMm2")
    if volume_mm3:
        defaults["weight_g"] = round(volume_mm3 / 1000 * material["density_g_cm3"], 2)
    if step_result.get("lengthMm") is not None:
        defaults["length_mm"] = float(step_result["lengthMm"])
    if step_result.get("widthMm") is not None:
        defaults["width_mm"] = float(step_result["widthMm"])
    if step_result.get("heightMm") is not None:
        defaults["height_mm"] = float(step_result["heightMm"])
    if surface_area_mm2:
        defaults["surface_area_cm2"] = round(surface_area_mm2 / 100, 2)
    return defaults


def _to_g(value: float, unit: str) -> float:
    return value * 1000 if unit == "kg" else value


def _to_yuan_kg(value: float, unit: str) -> float:
    return value * 1000 if unit == "元/g" else value


def _to_mm(value: float, unit: str) -> float:
    return value * 10 if unit == "cm" else value


def _to_cm2(value: float, unit: str) -> float:
    return value / 100 if unit == "mm²" else value


def _to_seconds(value: float, unit: str) -> float:
    return value * 60 if unit == "min" else value


if __name__ == "__main__":
    main()
