import os
import requests
import json
from typing import List
from dotenv import load_dotenv
from bs4 import BeautifulSoup
try:
    from IPython.display import Markdown, display, update_display
except Exception:
    Markdown = None
    display = None
    update_display = None
from openai import OpenAI
from rich.console import Console
from rich.markdown import Markdown
import markdown2

console = Console()

load_dotenv(override=True)
api_key = os.getenv('OPENAI_API_KEY')

if api_key and api_key.startswith('sk-proj-') and len(api_key)>10:
    print("API key Fetched")
else:
    print("There might be a problem with your API key? Please visit the troubleshooting notebook!")
    
MODEL = 'gpt-4o-mini'
openai = OpenAI()

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36"
}

class Website:
    def __init__(self, url):
        self.url = url
        response = requests.get(url, headers=headers)
        self.body = response.content
        soup = BeautifulSoup(self.body, 'html.parser')
        self.title = soup.title.string if soup.title else "No title found"
        if soup.body:
            for irrelevant in soup.body(["script", "style", "img", "input"]):
                irrelevant.decompose()
            self.text = soup.body.get_text(separator="\n", strip=True)
        else:
            self.text = ""
        links = [link.get('href') for link in soup.find_all('a')]
        self.links = [link for link in links if link]

    def get_contents(self):
        return f"Webpage Title:\n{self.title}\nWebpage Contents: \n{self.text}\n\n"
    

website_url = Website("https://roadmap.sh/guides/free-resources-to-learn-llms")
# print(website_url.links)


link_system_prompt = "You are provided with a list of links found on a webpage. \
You are able to decide which of the links would be most relevant to include in a brochure about the company, \
such as links to an About page, or a Company page, or Careers/Jobs pages.\n"
link_system_prompt += "You should respond in JSON as in this example:"
link_system_prompt += """
{
    "links": [
        {"type": "about page", "url": "https://full.url/goes/here/about"},
        {"type": "careers page", "url": "https://another.full.url/careers"}
    ]
}
"""

# print(link_system_prompt)

def get_links_user_prompt(website):
    user_prompt = f"Here is the list of links on the website of {website.url} - "
    user_prompt += "please decide which of these are relevant web link for a brocheure about the company, respond with the full https URL in JSON format. Do not include Terms of Service, Privacy, email links. \n"
    user_prompt += "Links (some might be relative links):\n"
    user_prompt += "\n".join(website.links)
    return user_prompt

# print(get_links_user_prompt(website_url))


def get_links(url):
    website = Website(url)
    response = openai.chat.completions.create(
        model= MODEL,
        messages=[
            {"role": "system", "content": link_system_prompt},
            {"role": "user", "content": get_links_user_prompt(website)}
        ],
            response_format={"type": "json_object"}
    )
    result = response.choices[0].message.content
    return json.loads(result)

hugginface = Website("https://huggingface.co")
hugginface.links

# print(get_links("https://huggingface.co"))


def get_all_details(url):
    result = "Landing page: \n"
    result += Website(url).get_contents()
    links = get_links(url)
    print("Found Links:" , links)
    for link in links["links"]:
        result += f"\n\n{link['type']}\n"
        result += Website(link["url"]).get_contents()
    return result

# print(get_all_details("https://huggingface.co"))

system_prompt= "You are an assistant that analyzes the contents of several relevant pages from a company website \
 and creates a short humorous, entertaining, jokey brochure about the company for prospective customers, investors and recruits. Respond in markdown.\
 Include details of company culture, customers and careers/jobs if you have the information."

def get_brocheture_ofcompany(company_name, url):
    user_prompt = f"You are looking at a company called: {company_name}\n"
    user_prompt += f"Here are the contents of the landing page and other relevant pages; use this infromation to build a short brocheture of the company in markdown.\n"
    user_prompt += get_all_details(url)
    user_prompt = user_prompt[:5_000]
    return user_prompt

def display_markdown(text):
    md = Markdown(text)
    console.print(md)

def create_brocheture(company_name, url):
    response = openai.chat.completions.create(
        model = MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": get_brocheture_ofcompany(company_name, url)}
        ]
    )
    result = response.choices[0].message.content
    display_markdown(result)
    return result
    


# create_brocheture("HuggingFace", "https://huggingface.co")
                  
def stream_brocheture(company_name, url):
    if display is None or update_display is None:
        return
    stream = openai.chat.completions.create(
        model = MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": get_brocheture_ofcompany(company_name, url)}
        ],
        stream=True
    )
    response = ""
    display_handle = display(display_markdown(""), display_id=True)
    for chunk in stream:
        response += chunk.choices[0].delta.content or ''
        response = response.replace("```","").replace("markdown", "")
        update_display(display_markdown(response), display_id=display_handle.display_id)

if __name__ == "__main__":
    stream_brocheture("HuggingFace", "https://huggingface.co")

#Creating PDF of multiple brocheture
# LOGO_URL = f"C:\\Users\\naman.sharma\\Downloads\\Nbglogo.jpg"
OUTPUT_DIR = "generated_brochures"
os.makedirs(OUTPUT_DIR, exist_ok=True)


def markdown_to_styled_pdf(markdown_text, output_file, company_name):
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import LETTER
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, ListFlowable, ListItem
    from reportlab.lib.units import inch
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('Title', parent=styles['Title'], textColor=colors.HexColor('#1e3a8a'))
    h2_style = ParagraphStyle('Heading2', parent=styles['Heading2'], textColor=colors.HexColor('#1e3a8a'))
    body_style = ParagraphStyle('Body', parent=styles['BodyText'], leading=16, fontSize=11)
    doc = SimpleDocTemplate(output_file, pagesize=LETTER, leftMargin=0.8*inch, rightMargin=0.8*inch, topMargin=0.9*inch, bottomMargin=0.9*inch)
    elements = []
    if company_name:
        elements.append(Paragraph(company_name + " – Brochure", title_style))
        elements.append(Spacer(1, 0.2*inch))
    text = markdown_text or ""
    lines = text.splitlines()
    bullets = []
    def flush_bullets():
        if bullets:
            items = [ListItem(Paragraph(b, body_style)) for b in bullets]
            elements.append(ListFlowable(items, bulletType='bullet'))
            elements.append(Spacer(1, 0.12*inch))
            bullets.clear()
    for line in lines:
        l = line.strip()
        if not l:
            flush_bullets()
            elements.append(Spacer(1, 0.12*inch))
            continue
        if l.startswith('### '):
            flush_bullets()
            elements.append(Paragraph(l[4:], h2_style))
            elements.append(Spacer(1, 0.08*inch))
        elif l.startswith('## '):
            flush_bullets()
            elements.append(Paragraph(l[3:], h2_style))
            elements.append(Spacer(1, 0.08*inch))
        elif l.startswith('# '):
            flush_bullets()
            elements.append(Paragraph(l[2:], title_style))
            elements.append(Spacer(1, 0.1*inch))
        elif l.startswith(('-', '*')) and len(l) > 1:
            bullets.append(l[1:].strip())
        else:
            flush_bullets()
            elements.append(Paragraph(l, body_style))
    flush_bullets()
    doc.build(elements)


def generate_brochure(company_name, url):
    print(f"📄 Generating brochure for: {company_name}")
    markdown_content = create_brocheture(company_name, url)
    pdf_filename = os.path.join(OUTPUT_DIR, f"{company_name.lower().replace(' ', '_')}_brochure.pdf")
    markdown_to_styled_pdf(markdown_content, pdf_filename, company_name)
    print(f"✅ Saved: {pdf_filename}")


# 🔁 Generate brochures for multiple companies
companies = [
    {"name": "HuggingFace", "url": "https://huggingface.co"},
    {"name": "OpenAI", "url": "https://openai.com"},
    {"name": "Weights & Biases", "url": "https://wandb.ai"}
]

for company in companies:
    if __name__ == "__main__":
        generate_brochure(company["name"], company["url"])
