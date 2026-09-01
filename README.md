**Looking to download and install the Comic Vine Scraper plugin?  [Click here](https://github.com/cbanack/comic-vine-scraper/wiki/) to get started.**

------------------------------------------------------------------------------------

## About This Fork

This is a fork of Cory Banack's [comic-vine-scraper](https://github.com/cbanack/comic-vine-scraper),
maintained for use with [ComicRackCE](https://github.com/maforget/ComicRackCE). The upstream project
is in maintenance-only mode (no new features), so this fork adds several usability improvements to the
series/issue picker dialogs on top of the original v1.0.102 release:

- **Issue picker (IssueForm):**
  - New **Year** and **Month** columns, sourced from each issue's Comic Vine cover date
  - A filterable header row (Issue / Title / Year / Month), debounced so typing quickly in a
    500+-issue series doesn't lag
  - **"Previous Comic"** button: lets you go back and redo the immediately-previous book if you
    picked the wrong series/issue for it, including reverting its scraped count and forcing a real
    (non-cached) rescrape instead of silently reusing the earlier, wrong choice
  - A resizable window with a responsive, docked layout instead of a fixed size
- **Series picker (SeriesForm):**
  - Shift-click multi-column sorting on the series table (click sorts by one column, shift-click
    adds/toggles a tie-breaker column) on top of the existing filterable Series/Year/Issues/Publisher
    header row (also now debounced)
  - An editable "issue number to preview" field under the series cover art -- lets you correct the
    auto-detected issue number to preview a different cover, and that corrected number is then used
    (instead of the original guess) when picking the matching issue for the book
- **Search dialog:** the search box is now a combobox that remembers your last 20 (deduplicated)
  search terms, most-recent first
- **Performance:** a series' full issue list is now cached to disk for 24 hours, so re-scraping many
  books from the same large series doesn't re-fetch it from the Comic Vine API every time
- **Fix:** Ctrl+Backspace was inserting a stray control character instead of deleting the previous
  word in the new filter/search text boxes; now deletes the word as expected

This fork keeps the upstream project's source layout (`src/py/...`) so patches can still be diffed
against/contributed back to the original where it makes sense. See the original project's own
[Pull Requests](#pull-requests) policy below before proposing changes there.

------------------------------------------------------------------------------------

## Project Status

I am maintaining the Comic Vine Scraper project, but **I am no longer actively adding new features.**

The [latest release](https://github.com/cbanack/comic-vine-scraper/wiki/Download-and-Installation) of this app is functional as of March 2024, and should remain usable for the foreseeable future.  As my schedule permits, I will continue to provide minor maintenance patches and bugfixes to keep things running smoothly.   I will not be adding new features, however, and I do not have time to review or maintain large pull requests.

The code here provides a solid example of how to properly use the [Comic Vine API](https://comicvine.gamespot.com/api/), should you happen to want to create your own project that does that.   Also, if you are a relatively experienced python developer and you're interested in taking over Comic Vine Scraper, please feel free create your own fork and run with it!

For those of you who've used and supported Comic Vine Scraper over the last 15 years, you have my sincere thanks for all your efforts and kind words.  Here's to 15 more!

-Cory

------------------------------------------------------------------------------------

## Docs and Binaries

All documentation about this project, including the latest downloads and installation instructions
can be found on the Comic Vine Scraper [Wiki page](https://github.com/cbanack/comic-vine-scraper/wiki/).

### Technical Details
 
This project is written for Windows, using IronPython and the .NET library.  It displays WinForms graphics and makes heavy use of the [ComicVine REST API](https://www.comicvine.gamespot.com/api/).  It is a _plugin_ for the [ComicRackCE](https://github.com/maforget/ComicRackCE) comic book reader, which is a standalone Windows desktop application.  Except during development (see below), Comic Vine Scraper does _not_ run outside of ComicRackCE's plugin environment.   

This project is currently set up to compile and run in the [VS Code](https://code.visualstudio.com/) IDE using the [Microsoft Python Extension](https://marketplace.visualstudio.com/items?itemName=ms-python.python) with properly installed versions of both Python (for parsing source code in the IDE) and IronPython (for running the code using .NET assemblies).  In other words, you should have _ipy.exe_, _python.exe_, and _pylint.exe_ working on your command-line before you get started.

You should also get Java and Ant (i.e. _java.exe_ and _ant.exe_) installed and running, since this project uses Ant to build, test, and run the plugin during development.

All IronPython code is currently written for Python version 2, not 3.

### Pull Requests

At this point, I am not accepting large pull requests -- if you want to make major changes, please feel free to create your own fork!  Comic Vine Scraper is a stable, mature project and my work on it these days is simply maintenance and bug fixing.  I'm likely to accept well-written pull requests for straightforward fixes and small improvements, but _please contact me_ before you start doing any major work.

### License 

This project is created and distributed under the [Apache 2.0 License](https://www.apache.org/licenses/LICENSE-2.0).
This is an open source license, so you are welcome to create, build, and maintain your own fork of the codebase if you have a major enhancement that you want to add, or a wild new direction that you'd like to take the project.

    Unless required by applicable law or agreed to in writing, software 
    distributed under this License is distributed on an "AS IS" BASIS,
    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
    See the License for the specific language governing permissions and
    limitations under the License.
