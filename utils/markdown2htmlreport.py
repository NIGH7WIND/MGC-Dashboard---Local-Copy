import markdown

def markdown_to_html(markdown_text):
    html_text = ""
    # Convert markdown text to HTML
    for line in markdown_text.split('\n'):
      html_text += markdown.markdown(line)

    # Define the pre HTML structure with head
    html_pre = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Report</title>
  <style>
    body {
      font-family: Arial, sans-serif;
      margin: 0;
      padding: 10px;
      background-color: #f4f4f4;
      color: #333;
    }

    h1 {
      text-align: center;
      margin-bottom: 20px;
      color: #2c3e50;
      font-size: 32px;
      font-weight: bold;
    }

    h2 {
      margin-top: 30px;
      margin-bottom: 15px;
      font-size: 24px;
      color: #2980b9;
      border-bottom: 2px solid #2980b9;
      padding-bottom: 5px;
    }

    p {
      margin-left: 20px;
      margin-bottom: 20px;
      font-size: 18px;
      line-height: 1.6;
    }

    ul {
      list-style-type: disc;
      padding-left: 20px;
      margin: 0;
    }

    li {
      margin-left: 20px;
      margin-bottom: 10px;
      font-size: 16px;
      line-height: 1.5;
    }

    a {
      text-decoration: none;
      color: #477ee4;
      font-weight: normal;
    }

    a:hover {
      color: #23527c;
      text-decoration: underline;
    }

    hr {
      border: none;
      height: 1px;
      background-color: #ccc;
      margin: 20px 0;
    }

    .container {
      max-width: 900px;
      margin: 40px auto;
      padding: 30px;
      background-color: #fff;
      border: 1px solid #ddd;
      border-radius: 8px;
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
    }

    strong {
      font-weight: bold;
    }

    p strong {
      color: #2c3e50;
    }

    p em {
      font-style: italic;
      color: #7f8c8d;
    }

    h1,
    h2 {
      font-family: "Segoe UI", Tahoma, Geneva, Verdana, sans-serif;
    }

    @media (max-width: 768px) {
      .container {
        padding: 20px;
      }

      h1 {
        font-size: 28px;
      }

      h2 {
        font-size: 20px;
      }

      p,
      ul {
        font-size: 14px;
      }
    }
  </style>
</head>
<body>
  <div class="container">"""

    html_post = "</div></body></html>"

    # Combine the pre HTML, converted markdown to HTML, and post HTML
    return html_pre + html_text + html_post

# Example usage
with open(r"E:\Intern\Minerva\Final_Dashboard_GIT\financial_report_debug.md", "r") as file:
    markdown_text = file.read()

html_output = markdown_to_html(markdown_text)

# Save the HTML output to a file
output_path = "financial_report.html"  # You can specify a full path here if needed
with open(output_path, "w", encoding="utf-8") as html_file:
    html_file.write(html_output)

print(f"Report saved as {output_path}")
