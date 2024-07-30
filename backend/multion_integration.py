import os
from dotenv import load_dotenv
from multion.client import MultiOn
from datetime import datetime, timedelta
import backend.models as models

load_dotenv()

class MultiOnAPI:
    def __init__(self):
        self.client = MultiOn(
            api_key=os.getenv('MULTION_API_KEY')
        )

    def get_latest_headline(self, category):
        # Check if we have a recent headline in the database
        print(category)
        stored_headline = models.get_headline(category['id'])
        if stored_headline:
            fetched_at = datetime.fromisoformat(stored_headline['fetched_at'].replace('Z', '+00:00'))
            if (datetime.now(fetched_at.tzinfo) - fetched_at) < timedelta(days=1):
                return stored_headline
        
        create_response = self.client.sessions.create(
            url="https://www.google.com",
            include_screenshot=True
        )
        session_id = create_response.session_id

        status = "CONTINUE"
        while status == "CONTINUE":
            step_response = self.client.sessions.step(
                session_id=session_id,
                cmd=f"Search for the top SINGLE news article for {category}. Don't open any news websites.",
                include_screenshot=True
            )
            status = step_response.status
            print(f"Step response: {step_response}")

        retrieve_response = self.client.retrieve(
            session_id=session_id,
            cmd="Get the news article with their headlines, categories, and urls.",
            fields=["headline", "category", "url"],
            scroll_to_bottom=True,
            render_js=True
        )

        data = retrieve_response.data[0] if retrieve_response.data else None
        if data:
            data['fetched_at'] = datetime.now()
            models.save_headline(category['id'], data)
        return data

multion_api = MultiOnAPI()

    # def summarize_article(self, article):
    #     try:
    #         article_summary_response = self.client.retrieve(
    #             url=article["url"],
    #             cmd="Get a brief summary of this article in one or two sentences.",
    #             fields=["summary"]
    #         )
    #         summary = article_summary_response.data[0]["summary"]
    #         return {**article, "summary": summary}
    #     except Exception as e:
    #         print(f"Error summarizing article: {str(e)}")
    #         return article

    # def get_news_with_summaries(self, categories):
    #     headlines = self.get_latest_headlines(categories)
    #     with ThreadPoolExecutor() as executor:
    #         summaries = list(executor.map(self.summarize_article, headlines))
    #     return summaries

