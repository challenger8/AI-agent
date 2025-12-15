"""
utils/embedding_text_formatter.py
---------------------------------
Centralized text formatting for embedding generation.
Converts CRM entities (deals, activities, agents) to formatted text.
"""

from typing import Dict, Any


class EmbeddingTextFormatter:
    """
    Formats CRM entities into text suitable for embedding generation.

    This centralized utility ensures consistent text formatting
    across all embedding services.
    """

    SEPARATOR = " | "

    @classmethod
    def format_deal(cls, deal: Dict[str, Any]) -> str:
        """
        Convert deal to searchable text.

        Args:
            deal: Deal dictionary

        Returns:
            Formatted text for embedding
        """
        text_parts = [
            f"Deal: {deal.get('title', 'N/A')}",
            f"Status: {deal.get('status', 'N/A')}",
            f"Value: {deal.get('value', 0)}",
            f"Customer: {deal.get('customer_name', 'N/A')}",
            f"Description: {deal.get('description', '')}",
        ]
        return cls.SEPARATOR.join(filter(None, text_parts))

    @classmethod
    def format_activity(cls, activity: Dict[str, Any]) -> str:
        """
        Convert activity to searchable text.

        Args:
            activity: Activity dictionary

        Returns:
            Formatted text for embedding
        """
        text_parts = [
            f"Activity: {activity.get('type', 'N/A')}",
            f"Agent: {activity.get('agent_name', 'N/A')}",
            f"Date: {activity.get('activity_date', 'N/A')}",
            f"Notes: {activity.get('notes', '')}",
            f"Outcome: {activity.get('outcome', '')}",
        ]
        return cls.SEPARATOR.join(filter(None, text_parts))

    @classmethod
    def format_agent(cls, agent: Dict[str, Any]) -> str:
        """
        Convert agent to searchable text.

        Args:
            agent: Agent dictionary

        Returns:
            Formatted text for embedding
        """
        text_parts = [
            f"Agent: {agent.get('name', 'N/A')}",
            f"Email: {agent.get('email', 'N/A')}",
            f"Phone: {agent.get('phone', 'N/A')}",
            f"Title: {agent.get('title', 'N/A')}",
        ]
        return cls.SEPARATOR.join(filter(None, text_parts))