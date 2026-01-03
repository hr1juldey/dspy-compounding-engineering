"""
Dynamic batch size benchmarking for optimal embedding performance.

This test measures machine capabilities and sets OPTIMAL_BATCH_SIZE.
Run during setup or when changing hardware/models.
"""

import os
import time

import pytest


@pytest.mark.benchmark
def test_determine_optimal_batch_size():
    """
    Benchmark machine to find optimal batch size for embeddings.

    Strategy:
    1. Measure CPU cores and available memory
    2. Test small embedding batches to estimate throughput
    3. Calculate optimal batch size based on saturation point
    4. Set OPTIMAL_BATCH_SIZE environment variable

    Skip if embedding provider not available.
    """
    try:
        from utils.knowledge.embeddings.provider import DSPyEmbeddingProvider as EmbeddingProvider

        provider = EmbeddingProvider()
    except Exception as e:
        pytest.skip(f"Embedding provider not available: {e}")

    # Test sample texts
    sample_texts = [f"Sample text number {i} for benchmark testing." for i in range(100)]

    # Benchmark different batch sizes
    batch_sizes_to_test = [10, 25, 50, 75, 100]
    results = {}

    print("\n" + "=" * 60)
    print("BATCH SIZE BENCHMARK")
    print("=" * 60)

    for batch_size in batch_sizes_to_test:
        try:
            # Test this batch size
            test_batch = sample_texts[:batch_size]

            start = time.time()
            if hasattr(provider, "get_embeddings_batch"):
                provider.get_embeddings_batch(test_batch)
            else:
                # Fallback to serial
                for text in test_batch:
                    provider.get_embedding(text)
            elapsed = time.time() - start

            throughput = batch_size / elapsed  # texts per second
            results[batch_size] = throughput

            print(f"Batch size {batch_size:3d}: {throughput:6.2f} texts/sec ({elapsed:.2f}s)")

        except Exception as e:
            print(f"Batch size {batch_size:3d}: FAILED - {e}")
            results[batch_size] = 0

    # Find optimal batch size (highest throughput)
    if results:
        optimal_size = max(results.keys(), key=lambda k: results[k])
        optimal_throughput = results[optimal_size]

        print("=" * 60)
        print(f"OPTIMAL BATCH SIZE: {optimal_size} ({optimal_throughput:.2f} texts/sec)")
        print("=" * 60)

        # Write to .env file if it exists
        env_path = ".env"
        if os.path.exists(env_path):
            # Read existing .env
            with open(env_path, "r") as f:
                lines = f.readlines()

            # Update or append OPTIMAL_BATCH_SIZE
            found = False
            for i, line in enumerate(lines):
                if line.startswith("OPTIMAL_BATCH_SIZE="):
                    lines[i] = f"OPTIMAL_BATCH_SIZE={optimal_size}\n"
                    found = True
                    break

            if not found:
                lines.append("\n# Auto-detected optimal batch size for embeddings\n")
                lines.append(f"OPTIMAL_BATCH_SIZE={optimal_size}\n")

            # Write back
            with open(env_path, "w") as f:
                f.writelines(lines)

            print(f"\n✅ Updated .env with OPTIMAL_BATCH_SIZE={optimal_size}")
        else:
            print(f"\n⚠️  No .env file found. Please set OPTIMAL_BATCH_SIZE={optimal_size} manually")

        # Also set in current environment
        os.environ["OPTIMAL_BATCH_SIZE"] = str(optimal_size)

    else:
        pytest.fail("All batch sizes failed benchmarking")


@pytest.mark.benchmark
def test_measure_machine_specs():
    """
    Measure and report machine specifications for batch sizing.

    Reports:
    - CPU cores
    - Available RAM
    - Embedding provider and model
    - Recommended batch size range
    """
    import multiprocessing
    import platform

    try:
        import psutil

        memory_gb = psutil.virtual_memory().total / (1024**3)
        available_gb = psutil.virtual_memory().available / (1024**3)
    except ImportError:
        memory_gb = "unknown"
        available_gb = "unknown"

    cpu_count = multiprocessing.cpu_count()

    print("\n" + "=" * 60)
    print("MACHINE SPECIFICATIONS")
    print("=" * 60)
    print(f"Platform: {platform.system()} {platform.release()}")
    print(f"CPU Cores: {cpu_count}")
    print(
        f"Total RAM: {memory_gb:.1f} GB" if isinstance(memory_gb, float) else "Total RAM: unknown"
    )
    print(
        f"Available RAM: {available_gb:.1f} GB"
        if isinstance(available_gb, float)
        else "Available RAM: unknown"
    )

    try:
        from utils.knowledge.embeddings.provider import DSPyEmbeddingProvider as EmbeddingProvider

        provider = EmbeddingProvider()
        print(f"\nEmbedding Provider: {provider.embedding_provider}")
        print(f"Embedding Model: {provider.embedding_model_name}")
        print(f"Vector Size: {provider.vector_size}")
    except Exception as e:
        print(f"\nEmbedding Provider: Not available ({e})")

    # Recommendation based on specs
    if isinstance(memory_gb, float):
        if memory_gb < 8:
            rec_batch = "10-25 (low memory)"
        elif memory_gb < 16:
            rec_batch = "25-50 (medium memory)"
        elif memory_gb < 32:
            rec_batch = "50-75 (high memory)"
        else:
            rec_batch = "75-100 (very high memory)"

        print(f"\nRecommended Batch Size: {rec_batch}")

    print("=" * 60)


if __name__ == "__main__":
    # Run benchmarks directly
    test_measure_machine_specs()
    test_determine_optimal_batch_size()
