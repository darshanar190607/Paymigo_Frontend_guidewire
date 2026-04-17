import sys
try:
    import kaggle
    print("Import successful")
except Exception as e:
    print(f"Exception caught: {e}")
except BaseException as e:
    print(f"BaseException caught: {type(e).__name__}")
print("Script continued")
