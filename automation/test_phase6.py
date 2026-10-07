from __future__ import annotations

from time import sleep

from automation.latency_profiler import LatencyProfiler
from automation.parallel import (
    ParallelOperation,
    ParallelSafetyAnalyzer,
)
from automation.async_executor import AsyncExecutor
from automation.fast_response import (
    FastResponseEngine,
)
from automation.observation_cache import (
    ObservationCache,
)
from automation.tts_latency import (
    TTSResponsivenessTracker,
)
from automation.cancellation import (
    CancellationContext,
)
from automation.resource_manager import (
    ResourceManager,
)
from automation.timeout import (
    TimeoutManager,
)


def main():

    print("=" * 70)
    print("JARVIS X - PHASE 6.10 VALIDATION")
    print("=" * 70)

    ############################################################
    # 1. LATENCY PROFILING
    ############################################################

    profiler = LatencyProfiler()

    with profiler.measure(
        "validation"
    ):
        _ = sum(
            range(1000)
        )

    assert profiler.latest(
        "validation"
    ) is not None

    assert (
        profiler.summary()[
            "validation"
        ]["count"]
        ==
        1.0
    )

    print("[PASS] Latency profiling")

    ############################################################
    # 2. PARALLEL SAFETY
    ############################################################

    analyzer = ParallelSafetyAnalyzer()

    operations = [
        ParallelOperation(
            name="read_a",
            parallel_safe=True,
        ),
        ParallelOperation(
            name="read_b",
            parallel_safe=True,
        ),
    ]

    assert analyzer.can_parallelize(
        operations
    )

    dependent = ParallelOperation(
        name="dependent",
        dependencies=[
            "read_a"
        ],
        parallel_safe=True,
    )

    assert not analyzer.can_parallelize(
        operations + [dependent]
    )

    print("[PASS] Parallel safety analysis")

    ############################################################
    # 3. ASYNC EXECUTION
    ############################################################

    with AsyncExecutor(
        max_workers=2
    ) as executor:

        futures = [
            executor.submit(
                lambda value=value:
                    value * 2
            )

            for value in (
                1,
                2,
            )
        ]

        results = sorted(
            future.result()
            for future in futures
        )

    assert results == [
        2,
        4,
    ]

    print("[PASS] Async execution")

    ############################################################
    # 4. FAST RESPONSE
    ############################################################

    fast = FastResponseEngine().handle(
        "how are you"
    )

    assert fast.handled is True
    assert fast.answer

    slow = FastResponseEngine().handle(
        "explain quantum mechanics"
    )

    assert slow.handled is False

    print("[PASS] Fast local-response path")

    ############################################################
    # 5. OBSERVATION CACHE
    ############################################################

    captures = [
        0
    ]

    cache = ObservationCache(
        ttl_seconds=1.0
    )

    def capture():

        captures[0] += 1

        return {
            "screen":
                captures[0]
        }

    first = cache.get(
        capture
    )

    second = cache.get(
        capture
    )

    assert first == second
    assert captures[0] == 1

    cache.invalidate()

    third = cache.get(
        capture
    )

    assert third != first
    assert captures[0] == 2

    print("[PASS] Observation caching")

    ############################################################
    # 6. TTS RESPONSIVENESS TRACKING
    ############################################################

    tts_tracker = (
        TTSResponsivenessTracker()
    )

    metrics = tts_tracker.measure(
        text="Hello JARVIS.",
        prepare=lambda:
            "prepared",
        synthesize=lambda prepared:
            "audio",
        play=lambda audio:
            None,
    )

    assert metrics.first_audio_time >= 0.0

    assert (
        tts_tracker.summary()[
            "first_audio_average"
        ]
        >=
        0.0
    )

    print("[PASS] TTS responsiveness tracking")

    ############################################################
    # 7. CANCELLATION
    ############################################################

    cancellation = (
        CancellationContext()
    )

    assert cancellation.is_cancelled() is False

    cancellation.cancel(
        "Validation stop"
    )

    assert cancellation.is_cancelled() is True

    try:

        cancellation.check()

    except InterruptedError:

        pass

    else:

        raise AssertionError(
            "Cancellation check did not raise."
        )

    cancellation.reset()

    assert cancellation.is_cancelled() is False

    print("[PASS] Cancellation propagation")

    ############################################################
    # 8. RESOURCE MANAGEMENT
    ############################################################

    cleaned = [
        False
    ]

    def cleanup(resource):

        cleaned[0] = True

    manager = ResourceManager()

    manager.register(
        "test_resource",
        object(),
        cleanup=cleanup,
    )

    assert (
        "test_resource"
        in
        manager.names()
    )

    assert manager.release(
        "test_resource"
    )

    assert cleaned[0] is True

    print("[PASS] Resource management")

    ############################################################
    # 9. TIMEOUTS
    ############################################################

    timeout_manager = TimeoutManager()

    fast_result = timeout_manager.run(
        lambda:
            "done",
        1.0,
    )

    assert fast_result.success is True
    assert fast_result.timed_out is False

    slow_result = timeout_manager.run(
        lambda:
            sleep(0.20),
        0.05,
    )

    assert slow_result.success is False
    assert slow_result.timed_out is True

    print("[PASS] Reliability / timeouts")

    ############################################################
    # FINAL
    ############################################################

    print()

    print("=" * 70)

    print(
        "PHASE 6.10 VALIDATION PASSED"
    )

    print("=" * 70)


if __name__ == "__main__":

    main()