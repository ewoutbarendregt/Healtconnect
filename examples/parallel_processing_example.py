"""
Example: Parallel document processing with HealthConnect automation.

This script demonstrates how to use parallel processing to handle
multiple documents simultaneously.
"""
import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.main import HealthConnectAutomation
from src.config import Config


async def example_parallel_processing():
    """Example: Process documents in parallel batches."""

    # Initialize the automation
    app = HealthConnectAutomation()

    print("=" * 60)
    print("PARALLEL PROCESSING EXAMPLE")
    print("=" * 60)

    # Example 1: Default parallel processing (batch size 3)
    print("\n1. Processing with default batch size (3 documents at a time)")
    count = await app.process_all_documents(parallel=True)
    print(f"   Result: {count} documents processed\n")


async def example_sequential_processing():
    """Example: Process documents sequentially (one at a time)."""

    app = HealthConnectAutomation()

    print("=" * 60)
    print("SEQUENTIAL PROCESSING EXAMPLE")
    print("=" * 60)

    print("\nProcessing documents one at a time (safest option)")
    count = await app.process_all_documents(parallel=False)
    print(f"Result: {count} documents processed\n")


async def example_custom_batch_size():
    """Example: Process with custom batch size."""

    app = HealthConnectAutomation()

    print("=" * 60)
    print("CUSTOM BATCH SIZE EXAMPLE")
    print("=" * 60)

    # Example: Process 5 documents at a time
    batch_size = 5
    print(f"\nProcessing {batch_size} documents at a time")
    count = await app.process_all_documents(parallel=True, batch_size=batch_size)
    print(f"Result: {count} documents processed\n")


async def main():
    """Run examples."""

    # Set to simulation mode for testing
    Config.USE_SIMULATION = True

    print("\nHealthConnect Parallel Processing Examples")
    print("=" * 60)
    print("NOTE: These examples use the simulation app")
    print("      Set USE_SIMULATION=False for production")
    print("=" * 60)

    # Choose which example to run
    print("\nSelect an example:")
    print("1. Sequential processing (one at a time)")
    print("2. Parallel processing (default batch size 3)")
    print("3. Custom batch size (5 documents at a time)")
    print("4. All examples")

    choice = input("\nEnter choice (1-4): ").strip()

    if choice == "1":
        await example_sequential_processing()
    elif choice == "2":
        await example_parallel_processing()
    elif choice == "3":
        await example_custom_batch_size()
    elif choice == "4":
        print("\nRunning all examples...\n")
        await example_sequential_processing()
        await example_parallel_processing()
        await example_custom_batch_size()
    else:
        print("Invalid choice")
        sys.exit(1)

    print("\n" + "=" * 60)
    print("Examples completed!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
