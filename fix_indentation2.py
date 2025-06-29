#!/usr/bin/env python3

def fix_indentation():
    file_path = 'src/web/app.py'
    with open(file_path, 'r') as file:
        lines = file.readlines()
    
    # Fix the indentation issue around line 2135
    for i in range(len(lines)):
        if "raise e" in lines[i] and i > 2130 and i < 2140:
            # This is the problematic area - fix the indentation
            lines[i] = "        raise e\n"
            break
    
    with open(file_path, 'w') as file:
        file.writelines(lines)
    
    print("Indentation fixed in", file_path)

if __name__ == "__main__":
    fix_indentation()
