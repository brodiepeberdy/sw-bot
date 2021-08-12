import discord, requests, requests_cache
# For web scraping / handling the requested HTML
from bs4 import BeautifulSoup

class MyClient(discord.Client):
    requests_cache.install_cache('sw_cache', expire_after=604800)
    # Prints that the bot is logged in and ready for use.
    async def on_ready(self):
        print('Now logged on as:', self.user)
    async def on_message(self, message):
        # Won't reply to itself.
        if message.author.id == self.user.id:
            return
        # Explains each command's purpose.
        elif message.content.startswith('?help'):
            await message.reply("**SW Bot's Commands**"
            + "\n" + "`?help`" + " - An overview of what commands this bot uses."
            + "\n" + "`?search [QUERY]`" + " - If you're unsure on the spelling of an article's title, use this command to recieve the top five results for your search query."
            + "\n" + "`?overview [QUERY]`" + " - Provides an overview of the article you've specified. If you're unsure on the spelling of something (which will fail to retrieve the article), try the search function!."
            + "\n" + "`?info [QUERY]`" + " - Provides a summary paragraph for the article.")
        # Provides the overview of a queried wiki article.
        elif message.content.startswith('?overview'):
            try:
                # Strips the command, isolating the query / topic specified by the user.
                topic = message.content[10:]
                page = Scraper.scrape_wookieepedia("https://starwars.fandom.com/wiki/", topic)
                overview = Scraper.page_overview(page)
                overall_length = len(overview)
                current_length = 0
                current_msg = ""
                for para in overview:
                    if current_length + len(para) <= 2000:
                        current_msg = current_msg + para
                        current_length = current_length + len(para)
                    else:
                        await message.reply(current_msg)
                        current_msg = para
                        current_length = len(para)
                        if current_length > 2000:
                            await message.reply(current_msg[0:1980] + " [...] ```")
                            current_length = 0
                            current_msg = ""
                await message.reply(current_msg)

            except:
                await message.reply("Looks like I had an issue with your query, please try again. It's likely there is a mispelling, if you're unsure please use the search function! :)")

        elif message.content.startswith('?search'):
            try:
                # Strips the command, isolating the query / topic specified by the user.
                topic = message.content[8:]
                page = Scraper.scrape_wookieepedia("https://starwars.fandom.com/wiki/Special:Search?query=", topic)
                overview = Scraper.search_results(page)
                await message.reply(overview)
            except:
                await message.reply("Looks like I had an issue with your query, please try again. :)")
        elif message.content.startswith('?info'):
            try:
                # Strips the command, isolating the query / topic specified by the user.
                topic = message.content[6:]
                page = Scraper.scrape_wookieepedia("https://starwars.fandom.com/wiki/", topic)
                info = Scraper.page_info(page)
                await message.reply(info)
            except:
                await message.reply("Looks like I had an issue with your query, please try again. :)")

class Scraper():
    # Scrapes and returns a HTML page as a BeautifulSoup object.
    def scrape_wookieepedia(base, topic):
        url = base + topic
        request = requests.get(url)
        if request.status_code in [200]:
            page = BeautifulSoup(request.text, 'lxml')
            return page
    # Converts a list of li items into a comma separated string of items. Checks if a li contains a ul itself.
    def list_converter(ul, text):
        for li in ul:
            try:
                inner_list = ""
                for child in li.ul.children:
                    inner_list2 = ""
                    try:
                        for granchild in child.ul.children:
                            inner_list2 = inner_list2 + granchild.text + ", "
                    except:
                        pass
                    [u.extract() for u in child('ul')]
                    text = text + child.text + ", " + inner_list2
            except:
                pass
            [u.extract() for u in li('ul')]
            text = text + li.text + ", " + inner_list
        text = text[:-2] + "."
        return text
    # Returns the key information of an article.
    def page_overview(page):
        overview = page.find('aside', class_="portable-infobox")
        paras = []
        # Removes superscript tags and content from the HTML document.
        [s.extract() for s in overview('sup')]
        # Article Title
        text = "**" + overview.h2.text + "**"
        # The overview part of the article's page.
        sections  = overview.find_all('section')
        for section in sections:
            # Section Title
            try:
                text = text + "\n" + "***" + section.h2.string + "***" + "\n" + "```"
            except:
                try:
                    text = text + "\n" + "***" + section.table.caption.text + "***" + "\n" + "```"
                except:
                    text = text + "\n" + "```"

            # List of items contained within a div.
            try:
                original_text = text
                divs = section.find_all('div', class_="pi-item pi-data pi-item-spacing pi-border-color")
                for div in divs:
                    text = text + "\n" + div.h3.text + ": "
                    try:
                        text = Scraper.list_converter(div.div.ul.children, text)
                    except:
                        text = text + div.div.text + "."
                if original_text == text:
                    raise Exception
                text = text + " " + "```"
            except:
                # Scrollable tables
                try:
                    tds = section.table.tbody.tr.find_all('td', class_="pi-horizontal-group-item pi-data-value pi-font pi-border-color pi-item-spacing")
                    for td in tds:
                        try:
                            ul = td.ul
                        except:
                            ul = td.div.table.tr.td.div.ul
                        try:
                            text = Scraper.list_converter(ul, text)
                        except:
                            text = text + div.ul.text + "."
                        text = text + "\n\n"
                    text = text[:-2]
                    text = text + "```"
                except:
                    # Non-scrollable Table
                    try:
                        tds = section.table.tbody.find_all('td')
                        for td in tds:
                            text = text + td.text + "\n\n"
                        text = text[:-2] + "```"
                    except:
                        text = text + "```"
            paras.append(text)
            text = ""

        text = text + "\n" + overview.figure.a.img['src']
        paras.append(text)
        return paras

    # First paragraph of an article.
    def page_info(page):
        title = page.find('h1', class_="page-header__title").text
        info = page.find('aside', class_="portable-infobox").find_next('p').text
        text = "**" + title + "**" + "\n" + info
        return text[0:2000]
    # Top five results from a search query.
    def search_results(page):
        results_pane = page.find('div', class_="unified-search__layout__main")
        results  = results_pane.find_all('article')
        text = "**Search Results**" + "\n"
        no_results = 0
        for result in results:
            no_results = no_results + 1
            if no_results > 5:
                break;
            info = result.find('div', class_="unified-search__result__content")
            text = text + "**" + result.h1.text + "**" + "```" + info.text + "```"
        return text[0:2000]

client = MyClient()
client.run('')
