from cost_workbench.input_analysis import analyze_images, analyze_step_file, parse_step_geometry
from cost_workbench.material_library import (
    get_material,
    material_names_for_process,
)
from cost_workbench.process_routes import get_process_route


def test_material_selection_includes_injection_plastics_and_metals():
    injection_materials = material_names_for_process("注塑件")
    cnc_materials = material_names_for_process("CNC铝件")

    assert "ABS" in injection_materials
    assert "PC+ABS" in injection_materials
    assert "PA66+GF" in injection_materials
    assert "AL6061" in cnc_materials
    assert get_material("PC+ABS")["density_g_cm3"] > 0


def test_process_route_contains_detailed_sheet_metal_and_stamping_steps():
    sheet_route = get_process_route("钣金件")
    stamping_route = get_process_route("铝合金冲压")

    assert [step["name"] for step in sheet_route][:3] == ["开料", "冲孔/落料", "折弯"]
    assert any("折弯" in step["description"] for step in sheet_route)
    assert [step["name"] for step in stamping_route][:3] == ["卷料/板料备料", "开卷校平", "冲压落料"]
    assert all(step["cost_item"] for step in stamping_route)


def test_process_routes_module_imports_and_all_routes_have_steps():
    for process in ["注塑件", "CNC铝件", "铝合金冲压", "钣金件", "锌合金压铸", "3D打印"]:
        route = get_process_route(process)
        assert len(route) >= 5
        assert all({"name", "description", "risk", "cost_item", "geometry_basis"} <= set(step) for step in route)


def test_step_file_analysis_extracts_schema_and_entity_count_without_cad_kernel():
    step_text = b"""ISO-10303-21;
HEADER;
FILE_SCHEMA(('AP214'));
ENDSEC;
DATA;
#1=CARTESIAN_POINT('',(0.,0.,0.));
#2=CARTESIAN_POINT('',(1.,0.,0.));
ENDSEC;
END-ISO-10303-21;"""

    result = analyze_step_file("demo.step", step_text)

    assert result["file_name"] == "demo.step"
    assert result["extension"] == ".step"
    assert result["schema"] == "AP214"
    assert result["entity_count"] == 2
    assert result["status"] == "缺少几何内核"


def test_step_geometry_parser_uses_cadquery_like_importer():
    class FakeBoundingBox:
        xlen = 10.0
        ylen = 20.0
        zlen = 3.0

    class FakeShape:
        def BoundingBox(self):
            return FakeBoundingBox()

        def Volume(self):
            return 420.0

        def Area(self):
            return 260.0

    class FakeWorkplane:
        def val(self):
            return FakeShape()

    class FakeImporters:
        @staticmethod
        def importStep(path):
            assert path.endswith(".step")
            return FakeWorkplane()

    result = parse_step_geometry(
        "demo.step",
        b"ISO-10303-21; DATA; #1=CARTESIAN_POINT('',(0.,0.,0.)); ENDSEC;",
        importer=FakeImporters,
    )

    assert result["status"] == "解析成功"
    assert result["lengthMm"] == 10.0
    assert result["widthMm"] == 20.0
    assert result["heightMm"] == 3.0
    assert result["bboxVolumeMm3"] == 600.0
    assert result["volumeMm3"] == 420.0
    assert result["volumeUtilization"] == 0.7
    assert result["outerSurfaceAreaMm2"] == 260.0


def test_image_analysis_marks_uploaded_creo_views():
    images = [
        {"name": "front_view.png", "size": 1200},
        {"name": "iso_3d.png", "size": 3400},
        {"name": "section_detail.jpg", "size": 800},
    ]

    result = analyze_images(images)

    assert result["count"] == 3
    assert result["is_enough_for_report"] is True
    assert result["items"][0]["view_type"] == "前视图"
    assert result["items"][1]["view_type"] == "3D 视图"
    assert result["items"][2]["view_type"] == "剖视/局部细节"
