"""
Command handling for LINE Bot interactions.

This module defines and processes various user commands for restaurant
recommendation functionality, supporting both text-based commands and
location-based interactions.
"""

import logging
import re
from enum import Enum
from dataclasses import dataclass
from typing import Optional, List, Set

logger = logging.getLogger(__name__)


class CommandType(Enum):
    """Enumeration of supported bot commands."""
    RECOMMEND = "recommend"
    RANDOM = "random"
    HELP = "help"
    STATUS = "status"
    CLEAR = "clear"
    UNKNOWN = "unknown"


@dataclass
class Command:
    """
    Represents a parsed user command.
    
    Attributes:
        type: The type of command
        original_text: Original user input
        confidence: Confidence level of command parsing (0.0-1.0)
    """
    type: CommandType
    original_text: str
    confidence: float = 1.0
    
    def __str__(self) -> str:
        return f"{self.type.value}({self.confidence:.2f}): '{self.original_text}'"


class CommandParser:
    """
    Parses user input text into structured commands.
    
    Supports multiple languages and command variations for better UX.
    """
    
    def __init__(self):
        """Initialize the command parser with predefined patterns."""
        # Define command patterns with variations and synonyms
        self.command_patterns = {
            CommandType.RECOMMEND: [
                # Chinese patterns
                r"(?i)^(抽|抽餐廳|抽一家|推薦|推薦餐廳|找餐廳|吃什麼|吃啥|要吃什麼)$",
                r"(?i)^(來一家|再來一家|換一家|重新抽|再抽)$",
                # English patterns  
                r"(?i)^(recommend|recommendation|suggest|draw|random|pick)$",
                r"(?i)^(find.*restaurant|what.*eat|where.*eat)$",
                # Mixed patterns
                r"(?i)^(抽.*restaurant|推薦.*food|找.*eat)$",
            ],
            CommandType.HELP: [
                r"(?i)^(help|幫助|說明|指令|怎麼用|如何使用|\?)$",
                r"(?i)^(commands|功能|用法)$",
            ],
            CommandType.STATUS: [
                r"(?i)^(status|狀態|我的位置|現在位置|where.*am)$",
                r"(?i)^(location|地址|位置資訊)$",
            ],
            CommandType.CLEAR: [
                r"(?i)^(clear|清除|重設|reset|清空位置|刪除位置)$",
                r"(?i)^(重新設定|重來|重置)$",
            ]
        }
        
        logger.info("🎯 CommandParser initialized with multilingual patterns")
    
    def parse(self, text: str) -> Command:
        """
        Parse user input text into a Command object.
        
        Args:
            text: User input text
            
        Returns:
            Command object with parsed information
        """
        if not text or not text.strip():
            return Command(CommandType.UNKNOWN, text, 0.0)
        
        text = text.strip()
        
        # Try to match against each command type
        for command_type, patterns in self.command_patterns.items():
            for pattern in patterns:
                if re.search(pattern, text):
                    confidence = self._calculate_confidence(text, pattern)
                    logger.info(f"🎯 Parsed command: {command_type.value} from '{text}' (confidence: {confidence:.2f})")
                    return Command(command_type, text, confidence)
        
        # No pattern matched
        logger.info(f"❓ Unknown command: '{text}'")
        return Command(CommandType.UNKNOWN, text, 0.0)
    
    def _calculate_confidence(self, text: str, pattern: str) -> float:
        """
        Calculate confidence score for pattern match.
        
        Args:
            text: User input text
            pattern: Matched regex pattern
            
        Returns:
            Confidence score between 0.0 and 1.0
        """
        # Simple confidence calculation based on text length and pattern complexity
        base_confidence = 0.9
        
        # Exact matches get higher confidence
        if len(text) <= 10:  # Short, likely exact commands
            return min(base_confidence + 0.1, 1.0)
        
        # Longer text might be less precise
        return max(base_confidence - (len(text) * 0.01), 0.5)
    
    def get_help_text(self) -> str:
        """
        Get help text explaining available commands.
        
        Returns:
            Formatted help text
        """
        return """🤖 Whatever Eat 指令說明

📍 **設定位置**
傳送您的位置給我，我會記住 30 分鐘

🎲 **抽餐廳指令**
• 抽餐廳 / 推薦 / 吃什麼
• 來一家 / 再來一家 / 換一家
• recommend / random / pick

ℹ️ **其他指令**  
• 狀態 / status - 查看目前位置
• 清除 / clear - 清除位置記錄
• 幫助 / help - 顯示此說明

💡 **使用流程**
1️⃣ 先傳送您的位置
2️⃣ 輸入抽餐廳指令
3️⃣ 可重複抽取，無需重新設定位置"""


# Global command parser instance
command_parser = CommandParser()


def get_command_parser() -> CommandParser:
    """
    Get the global command parser instance.
    
    Returns:
        Global CommandParser instance
    """
    return command_parser