# 11.04.25


# External libraries
import httpx
from rich.console import Console


# Internal utilities
from StreamingCommunity.Util.config_json import config_manager
from StreamingCommunity.Util.headers import get_headers


# Variable
MAX_TIMEOUT = config_manager.get_int("REQUESTS", "timeout")
REQUEST_VERIFY = config_manager.get_bool('REQUESTS', 'verify')
console = Console()

class VideoSource:
   
    @staticmethod
    def extract_m3u8_url(video_url: str) -> str:
        """Extract the m3u8 streaming URL from a RaiPlay video URL."""
        if not video_url.endswith('.json'):
            if '/video/' in video_url:
                video_id = video_url.split('/')[-1].split('.')[0]
                video_path = '/'.join(video_url.split('/')[:-1])
                video_url = f"{video_path}/{video_id}.json"

            else:
                return "Error: Unable to determine video JSON URL"
                        
        try:
            response = httpx.get(video_url, headers=get_headers(), timeout=MAX_TIMEOUT, verify=REQUEST_VERIFY)
            response.raise_for_status()
                
            video_data = response.json()
            content_url = video_data.get("video").get("content_url")
            
            if not content_url:
                return "Error: No content URL found in video data"
                
            # Extract the element key
            if "=" in content_url:
                element_key = content_url.split("=")[1]
            else:
                return "Error: Unable to extract element key"
                
            # Request the stream URL
            params = {
                'cont': element_key,
                'output': '62',
            }
            stream_response = httpx.get('https://mediapolisvod.rai.it/relinker/relinkerServlet.htm', params=params, headers=get_headers(), timeout=MAX_TIMEOUT, verify=REQUEST_VERIFY)
            stream_response.raise_for_status()
                
            # Extract the m3u8 URL
            stream_data = stream_response.json()
            m3u8_url = stream_data.get("video")[0] if "video" in stream_data else None
            return m3u8_url
            
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                console.print("[yellow]Content not found (404). Video may not be available.[/yellow]")
                return "Error: Content not found (404)"
            elif e.response.status_code == 410:
                console.print("[red]Content no longer available (410 Gone). The video link may have expired or been removed.[/red]")
                console.print("[yellow]Tip: Try refreshing the video link or try again later.[/yellow]")
                return "Error: Content no longer available (410 Gone)"
            else:
                console.print(f"[red]HTTP error {e.response.status_code}: {e.response.text[:100]}[/red]")
                return f"Error: HTTP {e.response.status_code}"
            
        except Exception as e:
            console.print(f"[red]Unexpected error: {str(e)}[/red]")
            return f"Error: {str(e)}"
