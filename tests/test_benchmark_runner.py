from integrations.benchmark_runner import BenchmarkRunner, ModelResult


def adapter_a(case):
    return ModelResult("A", "cell-state", float(case), 1, uncertainty=0.1)


def adapter_b(case):
    return ModelResult("B", "cell-state", float(case) - 0.1, 1, uncertainty=0.2)


def test_runner_normalizes_and_ranks_models():
    report = BenchmarkRunner().run(
        "cell-state",
        [0.8, 0.9],
        {"A": adapter_a, "B": adapter_b},
    )
    assert [r.model for r in report.ranked()] == ["A", "B"]
    assert report.ranked()[0].sample_count == 2
    assert report.ranked()[0].uncertainty == 0.1
