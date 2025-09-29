import aiohttp
import asyncio
from typing import Dict, Optional

async def check_ban(uid: str) -> Optional[Dict]:
    """
    Check ban status for a Free Fire user ID
    
    Args:
        uid (str): Free Fire user ID
        
    Returns:
        Dict with ban information or None if failed
    """
    api_url = f"http://raw.thug4ff.com/check_ban/check_ban/{uid}"
    
    # Set timeout for the request
    timeout = aiohttp.ClientTimeout(total=10)
    
    try:
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(api_url) as response:
                # Raise an exception for bad status codes
                response.raise_for_status()
                
                # Parse JSON response
                response_data = await response.json()
                
                # Check if the API returned success status
                if response_data.get("status") == 200:
                    data = response_data.get("data")
                    if data:  # Ensure 'data' key exists and is not None
                        return {
                            "is_banned": data.get("is_banned", 0),
                            "nickname": data.get("nickname", ""),
                            "period": data.get("period", 0),
                            "region": data.get("region", "Unknown")
                        }
                
                # If status is not 200 or data is missing, return None
                return None
                
    except aiohttp.ClientError as e:
        print(f"API request failed for UID {uid}: {e}")
        return None
    except asyncio.TimeoutError:
        print(f"API request timed out for UID {uid}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred for UID {uid}: {e}")
        return None