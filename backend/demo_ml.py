"""Demo script showing IntelliTrace ML models in action.

Run with: python -m demo_ml
"""

from __future__ import annotations

import sys
import os
import uuid

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def print_header(title: str) -> None:
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


def print_section(title: str) -> None:
    print(f"\n--- {title} ---")


def demo_anomaly_detection():
    """Demo: Train and use the anomaly detection model."""
    print_header("ANOMALY DETECTION DEMO")
    print("Detects when the device is NOT being worn by the user.\n")

    from app.ml.shared.synthetic import generate_normal_wearing_data, generate_anomaly_data
    from app.ml.anomaly_detection.trainer import AnomalyTrainer
    from app.ml.anomaly_detection.predictor import AnomalyPredictor
    from app.ml.shared.preprocessing import extract_window_features

    device_id = uuid.uuid4()

    # Step 1: Generate synthetic training data
    print_section("Step 1: Generating synthetic training data")
    normal_data = generate_normal_wearing_data(device_id, num_readings=1000)
    print(f"  Generated {len(normal_data)} normal wearing readings")
    print(f"  Sample reading keys: {list(normal_data[0].keys())}")
    print(f"  Heart rates present: {sum(1 for r in normal_data if r['heart_rate'] is not None)}")

    # Step 2: Train the model
    print_section("Step 2: Training anomaly detection model")
    trainer = AnomalyTrainer()
    features = trainer.prepare_features([normal_data], window_size=50, step=10)
    print(f"  Extracted {len(features)} feature windows")
    print(f"  Feature keys: {list(features[0].keys())[:5]}...")

    result = trainer.train(features, model_name="demo_anomaly")
    print(f"  Training complete!")
    print(f"  Threshold: {result['threshold']:.6f}")
    print(f"  Mean error: {result['mean_error']:.6f}")
    print(f"  Training samples: {result['samples']}")

    # Step 3: Test with normal data
    print_section("Step 3: Testing with NORMAL wearing data")
    predictor = AnomalyPredictor()
    loaded = predictor.load("demo_anomaly")
    print(f"  Model loaded: {loaded}")

    test_normal = normal_data[500:550]  # 50 readings to match training window
    result_normal = predictor.predict(test_normal)
    print(f"  Is anomaly: {result_normal['is_anomaly']}")
    print(f"  Confidence: {result_normal['confidence']:.2%}")
    print(f"  AE error: {result_normal['ae_error']:.6f}")
    print(f"  Reason: {result_normal['reason']}")

    # Step 4: Test with anomaly data (device not worn)
    print_section("Step 4: Testing with ANOMALY data (device not worn)")
    anomaly_data = generate_anomaly_data(device_id, num_readings=50)
    result_anomaly = predictor.predict(anomaly_data)
    print(f"  Is anomaly: {result_anomaly['is_anomaly']}")
    print(f"  Confidence: {result_anomaly['confidence']:.2%}")
    print(f"  AE error: {result_anomaly['ae_error']:.6f}")
    print(f"  Reason: {result_anomaly['reason']}")

    # Summary
    print_section("Anomaly Detection Summary")
    print(f"  Normal data flagged as anomaly: {'YES (false positive!)' if result_normal['is_anomaly'] else 'NO (correct)'}")
    print(f"  Anomaly data flagged as anomaly: {'YES (correct)' if result_anomaly['is_anomaly'] else 'NO (missed!)'}")

    return result_normal, result_anomaly


def demo_person_verification():
    """Demo: Train and use the person verification model."""
    print_header("PERSON VERIFICATION DEMO")
    print("Verifies if the current wearer matches the enrolled user.\n")

    from app.ml.shared.synthetic import generate_normal_wearing_data, generate_different_person_data
    from app.ml.person_verification.trainer import PersonVerificationTrainer
    from app.ml.person_verification.predictor import PersonPredictor

    device_id = uuid.uuid4()

    # Step 1: Generate data for two people
    print_section("Step 1: Generating synthetic biometric data")
    user_data = [generate_normal_wearing_data(device_id, num_readings=300)]
    other_data = [generate_different_person_data(device_id, num_readings=300)]
    print(f"  Enrolled user: {len(user_data[0])} readings")
    print(f"  Other person: {len(other_data[0])} readings")

    # Step 2: Train the model
    print_section("Step 2: Training person verification model")
    trainer = PersonVerificationTrainer()
    pos_pairs, neg_pairs = trainer.prepare_pairs(user_data, other_data, seq_len=50)
    print(f"  Positive pairs: {len(pos_pairs)}")
    print(f"  Negative pairs: {len(neg_pairs)}")

    result = trainer.train(pos_pairs, neg_pairs, model_name="demo_verifier", epochs=20)
    print(f"  Training complete!")
    print(f"  Features: {result['n_features']}, Sequence length: {result['seq_len']}")

    # Step 3: Test with same user
    print_section("Step 3: Verifying ENROLLED user (should match)")
    predictor = PersonPredictor()
    loaded = predictor.load("demo_verifier")
    print(f"  Model loaded: {loaded}")

    current_readings = user_data[0][:150]
    baseline_readings = user_data[0][150:300]
    result_same = predictor.verify(current_readings, baseline_readings)
    print(f"  Matches: {result_same['matches']}")
    print(f"  Score: {result_same['score']:.4f}")
    print(f"  Threshold: {result_same['threshold']}")
    print(f"  Reason: {result_same['reason']}")

    # Step 4: Test with different person
    print_section("Step 4: Verifying DIFFERENT person (should NOT match)")
    other_readings = other_data[0][:150]
    result_diff = predictor.verify(other_readings, baseline_readings)
    print(f"  Matches: {result_diff['matches']}")
    print(f"  Score: {result_diff['score']:.4f}")
    print(f"  Threshold: {result_diff['threshold']}")
    print(f"  Reason: {result_diff['reason']}")

    # Summary
    print_section("Person Verification Summary")
    print(f"  Enrolled user verified: {'YES (correct)' if result_same['matches'] else 'NO (false reject!)'}")
    print(f"  Other person rejected: {'YES (correct)' if not result_diff['matches'] else 'NO (false accept!)'}")

    return result_same, result_diff


def main():
    print_header("INTELLITRACE ML DEMO")
    print("Smart Wearable Security & Health Monitoring System")
    print("Demonstrating Anomaly Detection + Person Verification models\n")

    try:
        # Run anomaly detection demo
        anomaly_normal, anomaly_result = demo_anomaly_detection()

        # Run person verification demo
        verify_same, verify_diff = demo_person_verification()

        # Final summary
        print_header("OVERALL RESULTS")
        anomaly_correct = (not anomaly_normal['is_anomaly']) and anomaly_result['is_anomaly']
        verify_correct = verify_same['matches'] and not verify_diff['matches']

        print(f"  Anomaly Detection: {'PASS' if anomaly_correct else 'NEEDS TUNING'}")
        print(f"  Person Verification: {'PASS' if verify_correct else 'NEEDS TUNING'}")

        if anomaly_correct and verify_correct:
            print("\n  All models working correctly!")
        else:
            print("\n  Some models may need more training data or threshold tuning.")
            print("  This is expected with small synthetic datasets.")

        print(f"\n  Models saved to: ./ml_models/")
        print(f"  To use in production, train with real telemetry data.\n")

    except Exception as e:
        print(f"\n  ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
