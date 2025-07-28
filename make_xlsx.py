import pandas as pd

data = {
    "Course Name": ["Example Course"],
    "Category": ["Electives (track)"],
    "ECs": [6],
    "Quarter": ["1, 2"],
    "Year": [1],
    "Selected? (Y/N)": [True],
    "Notes": [""],
    "Prerequisite": [""]
}

df = pd.DataFrame(data)
df.to_excel("courses.xlsx", sheet_name="courses_data", index=False)

print("Excel file created!")
