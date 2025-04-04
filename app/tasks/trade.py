import logging
from typing import Any

from app.worker import celery_app, run_async_task
from app.services.twitter import TwitterService
from app.services.sentiment import SentimentService
from app.services.blockchain import BlockchainService
from app.core.settings import settings


logger = logging.getLogger("sentiment_task")


async def execute_sentiment_analysis(
    netuid: int = 18, hotkey: str = "5FFApaS75bv5pJHfAp2FVLBj9ZaXuFDjEypsaBNc1wCfe52v"
) -> dict[str, Any]:
    """
    Analyze sentiment for tweets about a subnet and stake/unstake based on results.
    """
    logger.info(f"Executing sentiment analysis for subnet {netuid}")

    twitter_service = TwitterService(api_key=settings.DATURA_API_KEY.get_secret_value())
    sentiment_service = SentimentService(
        api_key=settings.CHUTES_API_KEY.get_secret_value()
    )
    blockchain_service = BlockchainService()

    try:
        tweets = await twitter_service.search_subnet_tweets(netuid=netuid)
        if not tweets or len(tweets) == 0:
            logger.warning(f"No tweets found for subnet {netuid}")
            return {"status": "no_data", "netuid": netuid, "reason": "No tweets found"}

        tweet_texts = twitter_service.extract_tweet_text(tweets)
        logger.info(f"Retrieved {len(tweet_texts)} tweets about subnet {netuid}")

        sentiment_score = await sentiment_service.analyze_sentiment(tweet_texts)
        logger.info(f"Sentiment score: {sentiment_score}")

        amount = abs(sentiment_score) * 0.01

        if sentiment_score > 0:
            logger.info(f"Positive sentiment ({sentiment_score}): Staking {amount} TAO")
            await blockchain_service.stake_tao(amount, hotkey, netuid)
            operation = "stake"
        else:
            logger.info(
                f"Negative sentiment ({sentiment_score}): Unstaking {amount} TAO"
            )
            await blockchain_service.unstake_tao(amount, hotkey, netuid)
            operation = "unstake"

        return {
            "status": "success",
            "netuid": netuid,
            "hotkey": hotkey,
            "operation": operation,
            "amount": amount,
            "sentiment_score": sentiment_score,
        }

    except Exception as e:
        logger.error(f"Error in sentiment analysis: {str(e)}")
        return {"status": "error", "netuid": netuid, "hotkey": hotkey, "error": str(e)}


@celery_app.task(name="analyze_sentiment_and_trade")
def analyze_sentiment_and_trade(
    netuid: int = 18, hotkey: str = "5FFApaS75bv5pJHfAp2FVLBj9ZaXuFDjEypsaBNc1wCfe52v"
) -> dict[str, Any]:
    """
    Celery task to analyze sentiment and execute a stake/unstake.
    Delegates to the async function by using the run_async_task helper.
    """
    return run_async_task.delay(
        "app.tasks.trade.execute_sentiment_analysis", netuid, hotkey
    ).get()
