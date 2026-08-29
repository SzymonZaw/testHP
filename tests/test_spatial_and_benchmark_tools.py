from integrations.spatial_and_benchmark_tools import TOOLS, get_tool, list_tools


def test_new_research_tools_are_registered():
    names = {tool.name for tool in TOOLS}
    assert {
        "Baysor",
        "ComSeg",
        "DISSECT",
        "spateo",
        "DeepLIIF",
        "NaVis",
        "Pantheon-LLM",
        "scFM-Bench",
        "scDrugPerturb-Bench",
        "DeepSpot",
    } <= names


def test_lookup_is_case_insensitive():
    assert get_tool("baysor").name == "Baysor"
    assert get_tool("PANTHEON-LLM").name == "Pantheon-LLM"


def test_categories_filter_tools():
    benchmarks = list_tools("benchmark")
    assert {tool.name for tool in benchmarks} == {"scFM-Bench", "scDrugPerturb-Bench"}
    assert all(tool.source.startswith("https://") for tool in TOOLS)
