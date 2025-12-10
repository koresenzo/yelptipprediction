import subprocess
import sys

def run_script(script_name):
    print("\n")
    print(f"Running {script_name}...")
    print("\n")
    
    result = subprocess.run([sys.executable, script_name], capture_output=False)
    
    if result.returncode != 0:
        print(f"\nThere was an error running {script_name}")
        sys.exit(1)
    
    print(f"\n{script_name} runs successfully")

if __name__ == "__main__":
    print("\n")
    print("Yelp Restaurant Tip Predictor")
    print("\n")
    
    scripts = [
        "data_loader.py",
        "sentiment_analysis.py",
        "prediction_model.py",
        "visualizations.py"
    ]
    
    for script in scripts:
        run_script(script)
    
    print("\n")
    print("Processing done")
    print("\n")

