import discord
from discord.ext import commands
from finvizfinance.quote import finvizfinance
from finvizfinance.insider import Insider
import logging
import sys
import pandas as pd

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("discord_bot.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("DiscordBot")

# Set up Discord bot with necessary intents
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix=';', intents=intents)

@bot.event
async def on_ready():
    """
    Event handler that runs when the bot successfully connects to Discord.
    Logs a confirmation message.
    """
    logger.info(f'{bot.user} has connected to Discord!')

@bot.event
async def on_message(message):
    """
    Event handler for incoming messages.
    Processes commands starting with ';'.
    
    Args:
        message (discord.Message): The incoming message object.
    """
    # Ignore messages from the bot itself
    if message.author == bot.user:
        return

    # Check if the message is a command (starts with ';')
    if message.content.startswith(';'):
        logger.info(f"Received command: {message.content}")
        parts = message.content[1:].split()
        if len(parts) == 2:
            ticker, command = parts
            if command.lower() == 'i':
                await send_insider_info(message.channel, ticker)
            else:
                await send_chart(message.channel, ticker, command)
        else:
            await message.channel.send("Invalid command. Use format: ;ticker command (e.g., ;aapl d, ;aapl w, ;aapl m, ;aapl i)")
            logger.warning(f"Invalid command received: {message.content}")

async def send_chart(channel, ticker: str, timeframe: str):
    """
    Fetches and sends a stock chart for the given ticker and timeframe.
    
    Args:
        channel (discord.TextChannel): The channel to send the chart to.
        ticker (str): The stock ticker symbol.
        timeframe (str): The chart timeframe ('d', 'w', or 'm').
    """
    logger.info(f"Sending chart for {ticker} with timeframe {timeframe}")
    timeframe = timeframe.lower()
    valid_timeframes = {
        'd': 'daily', 'w': 'weekly', 'm': 'monthly'
    }
    
    if timeframe in ['3', '5', '15']:
        await channel.send("Intraday charts (3, 5, 15 minutes) are only available for FINVIZ*Elite users. Please use 'd' for daily, 'w' for weekly, or 'm' for monthly charts.")
        logger.warning(f"Attempted to fetch intraday chart for {ticker}")
        return
    
    if timeframe not in valid_timeframes:
        await channel.send("Invalid timeframe. Use 'd' for daily, 'w' for weekly, or 'm' for monthly.")
        logger.warning(f"Invalid timeframe {timeframe} for {ticker}")
        return

    try:
        stock = finvizfinance(ticker)
        chart_url = stock.ticker_charts(timeframe=valid_timeframes[timeframe])
        
        embed = discord.Embed(title=f"{ticker.upper()} {valid_timeframes[timeframe]} Chart", color=0x00ff00)
        embed.set_image(url=chart_url)
        await channel.send(embed=embed)
        logger.info(f"Successfully sent chart for {ticker}")
    except Exception as e:
        await channel.send(f"An error occurred: {str(e)}")
        logger.error(f"Error sending chart for {ticker}: {str(e)}", exc_info=True)

async def send_insider_info(channel, ticker: str):
    """
    Fetches and sends insider trading information for the given ticker.
    
    Args:
        channel (discord.TextChannel): The channel to send the information to.
        ticker (str): The stock ticker symbol.
    """
    logger.info(f"Fetching insider info for {ticker}")
    try:
        stock = finvizfinance(ticker)
        fundament_info = stock.ticker_fundament()
        logger.debug(f"Fundament info fetched for {ticker}: {fundament_info}")
        
        insider_info = stock.ticker_inside_trader()
        logger.info(f"Insider info columns for {ticker}: {insider_info.columns.tolist()}")
        
        if insider_info.empty:
            await channel.send(f"No insider trading information found for {ticker.upper()}.")
            logger.warning(f"No insider trading information found for {ticker}")
            return
        
        # Create an embed for the insider information
        embed = discord.Embed(title=f"Insider trading information for {ticker.upper()}", color=0x00ff00)
        
        # Add fundament information
        for field in ['Company', 'Sector', 'Industry', 'Country']:
            if field in fundament_info:
                embed.add_field(name=field, value=fundament_info[field], inline=True)
        
        # Add insider trading information
        for _, row in insider_info.head(5).iterrows():
            insider_text = "\n".join([f"{col}: {row[col]}" for col in row.index if pd.notna(row[col])])
            embed.add_field(name="Insider Trade", value=insider_text, inline=False)
        
        await channel.send(embed=embed)
        logger.info(f"Successfully sent insider info for {ticker}")
    except Exception as e:
        await channel.send(f"An error occurred while fetching insider information: {str(e)}")
        logger.error(f"Error fetching insider info for {ticker}: {str(e)}", exc_info=True)

# Start the bot with the provided token
bot.run('YOUR_BOT_TOKEN_HERE')