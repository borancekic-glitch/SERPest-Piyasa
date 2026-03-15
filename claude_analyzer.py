import os
import anthropic

CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY", "").strip()

def analyze_news(headlines, known_stocks_text="", recent_memory_text="", feedback_text=""):
    client = anthropic.Anthropic(api_key=CLAUDE_API_KEY)

    prompt = f"""
You are an elite macro, geopolitical, and cross-market equity analyst.

Your job is to find:
- direct effects
- second-order effects
- third-order effects

You must think in chains like this:
event -> economic effect -> sector impact -> supplier / logistics / insurance / financing / infrastructure / software / niche public company benefit

Important rules:
1. Focus on U.S.-listed stocks.
2. Use the stock universe provided below when suggesting stocks.
3. Prefer realistic second-order and third-order beneficiaries.
4. Do not skip any section.
5. Give specific stock examples whenever possible.
6. Use recent memory to detect recurring themes.
7. Use past performance feedback carefully, but do not overfit.
8. Use ONLY the tickers provided in the stock universe list when suggesting stocks.
Do not invent new tickers.

Recent memory from previous days:
{recent_memory_text}

Past stock idea feedback:
{feedback_text}

Known stocks and sectors:
{known_stocks_text}

Today's news headlines:
{headlines}

Return your answer EXACTLY in this structure:

SUMMARY OF MAIN EVENT:
- Write 3-5 bullet points.

DIRECTLY AFFECTED INDUSTRIES:
- Industry:
  Why:
  Possible U.S. stocks:

SECOND-ORDER OPPORTUNITIES:
- Industry:
  Why it may benefit:
  Mechanism:
  Possible U.S. stocks:

THIRD-ORDER OPPORTUNITIES:
- Industry:
  Why it may benefit:
  Mechanism:
  Confidence level:
  Possible U.S. stocks:

RECURRING THEMES VS RECENT MEMORY:
- Write 2-4 bullet points.

LESSONS FROM PAST STOCK IDEA PERFORMANCE:
- Write 2-4 bullet points.

RISKS / WHY THE IDEA COULD FAIL:
- Write 3-5 bullet points.

BEST 3 IDEAS TODAY:
1. Stock / Industry:
   Thesis:
2. Stock / Industry:
   Thesis:
3. Stock / Industry:
   Thesis:
"""

    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1800,
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    return response.content[0].text