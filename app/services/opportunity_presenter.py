class OpportunityPresenter:

    @staticmethod
    def sentiment_label(value: int) -> str:
        if value >= 60:
            return "Bullish"
        if value >= 40:
            return "Neutral"
        return "Bearish"

    @staticmethod
    def media_buzz_label(value: float) -> str:
        if value >= 0.75:
            return "High"
        if value >= 0.40:
            return "Medium"
        return "Low"

    @staticmethod
    def technical_percent(technical_score: float) -> int:
        return round(
            max(
                0,
                min(
                    100,
                    (technical_score + 1) * 50
                )
            )
        )

    @staticmethod
    def technical_label(value: int) -> str:
        if value >= 70:
            return "Strong"
        if value >= 45:
            return "Moderate"
        return "Weak"

    @staticmethod
    def popularity_score(
        news_count: int,
        media_buzz: float
    ) -> int:
        return min(
            100,
            news_count * 10 + round(media_buzz * 50)
        )

    @staticmethod
    def main_catalyst(signals: list[dict]) -> str:
        if not signals:
            return "No catalyst"

        return signals[0]["title"]

    @staticmethod
    def ai_explanation(
        prediction: dict,
        technical: dict,
        news_count: int
    ) -> str:
        return (
            f"Kayro predicts a {prediction['direction'].lower()} move "
            f"over the next {prediction['time_horizon_days']} days. "
            f"The score is supported by a {technical['trend'].lower()} trend, "
            f"{news_count} recent news article(s), "
            f"and a model confidence of {prediction['confidence']:.1f}%."
        )
