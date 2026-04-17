import argparse
import json
import sys
from typing import Optional
from geotruth.engine import GeoTruthEngine
from geotruth.schemas import ClaimVector, WorkerProfile

def cli():
    parser = argparse.ArgumentParser(
        description="GeoTruth — Multi-Modal Environmental Coherence Verification CLI"
    )
    
    parser.add_index = False # Not needed for argparse
    
    parser.add_argument(
        "--claim", 
        type=str, 
        required=True, 
        help="Path to a JSON file containing the ClaimVector data."
    )
    parser.add_argument(
        "--profile", 
        type=str, 
        default=None, 
        help="Path to a JSON file containing the WorkerProfile data (optional)."
    )
    parser.add_argument(
        "--burst", 
        type=float, 
        default=0.0, 
        help="Current claim burst rate in the pincode (default: 0.0)."
    )
    parser.add_argument(
        "--json", 
        action="store_true", 
        help="Output results as raw JSON instead of human-readable text."
    )

    args = parser.parse_args()

    try:
        # Load Claim
        with open(args.claim, 'r') as f:
            claim_data = json.load(f)
        claim = ClaimVector(**claim_data)

        # Load Profile if provided
        profile = None
        if args.profile:
            with open(args.profile, 'r') as f:
                profile_data = json.load(f)
            profile = WorkerProfile(**profile_data)

        # Initialize Engine and Verify
        engine = GeoTruthEngine()
        result = engine.verify(claim, profile=profile, claim_burst_rate=args.burst)

        if args.json:
            print(result.model_dump_json(indent=2))
        else:
            print("\n" + "="*60)
            print(" GeoTruth Verification Result")
            print("="*60)
            print(f"Tier           : {result.tier.upper()}")
            print(f"Recommendation : {result.recommendation}")
            print(f"Coherence Score: {result.coherence_score}/100")
            print(f"Confidence     : {int(result.confidence * 100)}%")
            
            if result.flagged_signals:
                print(f"Flags          : {', '.join(result.flagged_signals)}")
            if result.sensor_gaps:
                print(f"Gaps           : {', '.join(result.sensor_gaps)}")
            print("="*60 + "\n")

    except FileNotFoundError as e:
        print(f"Error: File not found - {e.filename}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    cli()
