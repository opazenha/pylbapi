from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    RATE_LIMITING_ENABLE: bool = False
    RATE_LIMITING_FREQUENCY: str = "2/3seconds"
    
    # Background refresh service settings
    BG_REFRESH_SCRAPE_DELAY: int = 10  # Delay between scraping requests in seconds
    BG_REFRESH_CYCLE_DELAY: int = 6000  # Delay between refresh cycles in seconds
    BG_REFRESH_ENABLED: bool = True  # Whether background refresh is enabled


settings = Settings()
