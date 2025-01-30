# config.py atual >>> config-writer-py
# config.py Padrão :config-write-py --defaults ou :config-write-py -d 

config.load_autoconfig(False)

c.aliases = {'q': 'quit', 'w': 'session-save', 'wq': 'quit --save'}

# Setting dark mode
#config.set("colors.webpage.darkmode.enabled", True)

c.downloads.location.directory = '~/Downloads'

config.set('content.cookies.accept', 'all', 'chrome-devtools://*')
config.set('content.cookies.accept', 'all', 'devtools://*')

 
config.set("fileselect.handler", "external")
config.set("fileselect.single_file.command", ['kitty', '--class', 'ranger,ranger', '-e', 'ranger', '--choosefile', '{}'])
config.set("fileselect.multiple_files.command", ['kitty', '--class', 'ranger,ranger', '-e', 'ranger', '--choosefiles', '{}'])


c.url.searchengines = {'DEFAULT': 'https://google.com/search?q={}',
                       'yt': 'https://www.youtube.com/results?search_query={}',
                       'aw': 'https://wiki.archlinux.org/?search={}',
                       're': 'https://www.reddit.com/r/{}',}

c.url.start_pages = ["https://google.com/"] 

# c.url.default_page = 'https://start.duckduckgo.com/'
c.url.default_page = 'https://google.com/'

c.fonts.default_family = "JetBrainsMono"
c.fonts.default_size = '8pt'
c.fonts.completion.entry = '8pt "JetBrainsMono"'
c.fonts.debug_console = '8pt "JetBrainsMono"'
c.fonts.prompts = '8pt "JetBrainsMono"'
c.fonts.statusbar = '8pt "JetBrainsMono"'

c.colors.completion.fg = '#ABB2BF'
c.colors.completion.odd.bg = '#080808'
c.colors.completion.even.bg = '#080808'
c.colors.completion.category.fg = '#917699'
c.colors.completion.category.bg = '#080808'
c.colors.completion.item.selected.bg = '#345E81'
c.colors.completion.item.selected.fg = '#ffffff'
c.colors.completion.item.selected.border.bottom = '#345E81'
c.colors.completion.item.selected.border.top = '#345E81'
c.colors.hints.fg = '#ffffff'
c.colors.hints.bg = '#345E81'
c.colors.hints.match.fg = '#000000'
c.colors.messages.info.bg = '#080808'
c.colors.statusbar.normal.bg = '#080808'
c.colors.statusbar.insert.fg = '#6a89a2'
c.colors.statusbar.insert.bg = '#080808'
c.colors.statusbar.passthrough.bg = '#56B6C2'
c.colors.statusbar.command.bg = '#080808'
c.colors.statusbar.url.warn.fg = '#3f5261'
c.colors.tabs.bar.bg = '#080808'
c.colors.tabs.odd.bg = '#2b2b3b'
c.colors.tabs.even.bg = '#2b2b3b'
c.colors.tabs.selected.odd.bg = '#080808'
c.colors.tabs.selected.even.bg = '#080808'
c.colors.tabs.pinned.odd.bg = '#080808'
c.colors.tabs.pinned.even.bg = '#080808'
c.colors.tabs.pinned.selected.odd.bg = '#080808'
c.colors.tabs.pinned.selected.even.bg = '#080808'

c.content.blocking.adblock.lists = [
    "https://raw.githubusercontent.com/hectorm/hmirror/master/data/adaway.org/list.txt",
	"https://raw.githubusercontent.com/hectorm/hmirror/master/data/adblock-nocoin-list/list.txt",
	"https://raw.githubusercontent.com/hectorm/hmirror/master/data/adguard-cname-trackers/list.txt",
	"https://raw.githubusercontent.com/hectorm/hmirror/master/data/adguard-simplified/list.txt",
	"https://raw.githubusercontent.com/hectorm/hmirror/master/data/dandelionsprout-nordic/list.txt",
	"https://raw.githubusercontent.com/hectorm/hmirror/master/data/easylist/list.txt",
	"https://raw.githubusercontent.com/hectorm/hmirror/master/data/easylist-ara/list.txt",
	"https://raw.githubusercontent.com/hectorm/hmirror/master/data/easylist-bul/list.txt",
	"https://raw.githubusercontent.com/hectorm/hmirror/master/data/easylist-ces-slk/list.txt",
	"https://raw.githubusercontent.com/hectorm/hmirror/master/data/easylist-deu/list.txt",
	"https://raw.githubusercontent.com/hectorm/hmirror/master/data/easylist-fra/list.txt",
	"https://raw.githubusercontent.com/hectorm/hmirror/master/data/easylist-heb/list.txt",
	"https://raw.githubusercontent.com/hectorm/hmirror/master/data/easylist-ind/list.txt",
	"https://raw.githubusercontent.com/hectorm/hmirror/master/data/easylist-ita/list.txt",
	"https://raw.githubusercontent.com/hectorm/hmirror/master/data/easylist-kor/list.txt",
	"https://raw.githubusercontent.com/hectorm/hmirror/master/data/easylist-lav/list.txt",
	"https://raw.githubusercontent.com/hectorm/hmirror/master/data/easylist-lit/list.txt",
	"https://raw.githubusercontent.com/hectorm/hmirror/master/data/easylist-nld/list.txt",
	"https://raw.githubusercontent.com/hectorm/hmirror/master/data/easylist-por/list.txt",
	"https://raw.githubusercontent.com/hectorm/hmirror/master/data/easylist-rus/list.txt",
	"https://raw.githubusercontent.com/hectorm/hmirror/master/data/easylist-spa/list.txt",
	"https://raw.githubusercontent.com/hectorm/hmirror/master/data/easylist-zho/list.txt",
	"https://raw.githubusercontent.com/hectorm/hmirror/master/data/easyprivacy/list.txt",
	"https://raw.githubusercontent.com/hectorm/hmirror/master/data/eth-phishing-detect/list.txt",
	"https://raw.githubusercontent.com/hectorm/hmirror/master/data/gfrogeye-firstparty-trackers/list.txt",
	"https://raw.githubusercontent.com/hectorm/hmirror/master/data/hostsvn/list.txt",
	"https://raw.githubusercontent.com/hectorm/hmirror/master/data/kadhosts/list.txt",
	"https://raw.githubusercontent.com/hectorm/hmirror/master/data/matomo.org-spammers/list.txt",
	"https://raw.githubusercontent.com/hectorm/hmirror/master/data/mitchellkrogza-badd-boyz-hosts/list.txt",
	"https://raw.githubusercontent.com/hectorm/hmirror/master/data/pgl.yoyo.org/list.txt",
	"https://raw.githubusercontent.com/hectorm/hmirror/master/data/phishing.army/list.txt",
	"https://raw.githubusercontent.com/hectorm/hmirror/master/data/socram8888-notonmyshift/list.txt",
	"https://raw.githubusercontent.com/hectorm/hmirror/master/data/someonewhocares.org/list.txt",
	"https://raw.githubusercontent.com/hectorm/hmirror/master/data/spam404.com/list.txt",
	"https://raw.githubusercontent.com/hectorm/hmirror/master/data/stevenblack/list.txt",
	"https://raw.githubusercontent.com/hectorm/hmirror/master/data/ublock/list.txt",
	"https://raw.githubusercontent.com/hectorm/hmirror/master/data/ublock-abuse/list.txt",
	"https://raw.githubusercontent.com/hectorm/hmirror/master/data/ublock-badware/list.txt",
	"https://raw.githubusercontent.com/hectorm/hmirror/master/data/ublock-privacy/list.txt",
	"https://raw.githubusercontent.com/hectorm/hmirror/master/data/urlhaus/list.txt",
	"https://raw.githubusercontent.com/hectorm/hmirror/master/data/winhelp2002.mvps.org/list.txt" ]
