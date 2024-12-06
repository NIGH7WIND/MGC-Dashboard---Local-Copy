import os
import pandas as pd

def extract_qna_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Processes a DataFrame and extracts structured QnA data based on predefined questions.

    Parameters:
    ----------
    df : pd.DataFrame
        The input DataFrame containing QnA data, including columns starting with 'Q', 'date', and 'link'.

    Returns:
    -------
    pd.DataFrame
        A structured DataFrame with columns ["Question", "Date", "Link", "Answer"].
    """
    questions = {
        "Q1": "Are there any regulatory or legal issues faced by the Company or its subsidiaries?",
        "Q2": "Are there any legal issues faced by the promoters of the Company?",
        "Q3": "Has the Company faced employee attrition in the past and has the key management team changed in the past 2 years?",
        "Q4": "Is the industry in which Company operates facing a slowdown?",
        "Q5": "Is the Company overvalued as compared to its peers?",
        "Q6": "Are there any significant upcoming events or product launches that could impact the company’s performance?",
        "Q7": "Has the Company's revenues, operating profit margins, net profit margins grown year on year for past 3 years and are these better than industry growth rate?",
        "Q8": "Has the Company's debt increased or decreased over past 3 years?",
        "Q9": "Has the Company capacity utilization increased or decreased over past 3 years and how much capacity has the Company added in past 3 years?",
        "Q10": "Has the promoter stake in the Company increased or decreased in the past?",
        "Q11": "Has the institution stake in the Company increased or decreased in the past?",
        "Q12": "How many analysts are tracking the Company's stock and what is the percentage upside on target price given by the analysts?"
    }

    question_cols = [col for col in df.columns if col.startswith("Q")]
    question_cols.sort(key=len)

    structured_data = []
    for col in question_cols:
        question_text = questions.get(col)
        if question_text:
            structured_data.append([question_text, "", "", ""])
            for _, row in df.dropna(subset=[col]).iterrows():
                answer = row[col]
                if isinstance(answer, str) and answer.strip().startswith("N/A"):
                    continue
                date = row.get('date', "")
                link = row.get('link', "")
                structured_data.append(["", date, link, answer])
    
    extracted_df = pd.DataFrame(structured_data, columns=["Question", "Date", "Link", "Answer"])
    return extracted_df

def process_excel_file(file_path: str, output_dir: str = None) -> None:
    """
    Reads an Excel file, processes it for QnA data, and saves the output to a new file.

    Parameters:
    ----------
    file_path : str
        Path to the input Excel file.
    output_dir : str, optional
        Directory to save the processed output. Defaults to the input file's directory.

    Returns:
    -------
    None
    """
    try:
        df = pd.read_excel(file_path)
        extracted_df = extract_qna_data(df)

        # Prepare output path
        if output_dir is None:
            output_dir = os.path.dirname(file_path)
        output_filename = os.path.splitext(os.path.basename(file_path))[0] + "_QnA.xlsx"
        output_path = os.path.join(output_dir, output_filename)

        extracted_df.to_excel(output_path, index=False)
        print(f"Processed and saved: {output_path}")

    except Exception as e:
        print(f"Error processing file {file_path}: {e}")

# # Example usage
# file_path = r"E:\Intern\Minerva\LLM API\new\gemini_debugging_output.xlsx"
# process_excel_file(file_path)
