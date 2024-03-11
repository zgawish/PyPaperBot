# -*- coding: utf-8 -*-

import argparse
import sys
import os
from .Paper import Paper
from .PapersFilters import filterJurnals, filter_min_date, similarStrings
from .Downloader import downloadPapers
from .Scholar import ScholarPapersInfo
from .Crossref import getPapersInfoFromDOIs, getPapersInfoFromMixed
from .proxy import proxy

def start(query, scholar_results, scholar_pages, dwn_dir, proxy, min_date=None, num_limit=None, num_limit_type=None, filter_jurnal_file=None, restrict=None, DOIs=None, SciHub_URL=None, queries=None, query_pdf_names=None):
    to_download = []
    if DOIs is None and queries is None:
        print("Query: {}".format(query))
        to_download = ScholarPapersInfo(query, scholar_pages, restrict, min_date, scholar_results)
    elif DOIs is None and queries is not None:
        print("Downloading papers from queries\n")
        queries_found = 0
        queries_not_found = 0

        queries_found_list = []
        queries_not_found_list = []
        for query_idx, q in enumerate(queries):
            print("Query {}/{}: {}".format(query_idx, len(queries), query))
            queries_to_download = ScholarPapersInfo(q, scholar_pages, restrict, min_date, scholar_results)
            if len(queries_to_download) > 0:
                queries_found += 1
                queries_found_list.append(q)
                print("Query found {}/{}: {}".format(queries_found, len(queries), query))
            else:
                queries_not_found += 1
                queries_not_found_list.append(q)
                print("Query not found {}/{}: {}".format(queries_not_found, len(queries), query))
            for paper in queries_to_download:
                paper.title = query_pdf_names[query_idx]
                to_download.append(paper)
        print("Queries found: {}\nQueries not found:".format(queries_not_found, len(queries), query))
        f = open(dwn_dir+"queries_found.txt", 'wb')
        f.writelines(query_found + '\n' for query_found in queries_found)
        f.close()
        f = open(dwn_dir+"queries_not_found.txt", 'wb')
        f.writelines(query_not_found + '\n' for query_not_found in queries_not_found)
        f.close()
    else:
        print("Downloading papers from DOIs\n")
        num = 1
        i = 0
        while i < len(DOIs):
            DOI = DOIs[i]
            if len(DOI) == 2:
                print("Searching paper {} of {} with DOI {}".format(num, len(DOIs), DOI[1]))
                papersInfo = getPapersInfoFromMixed(DOI, restrict)
                to_download.append(papersInfo)
            else:
                print("Searching paper {} of {} with DOI {}".format(num, len(DOIs), DOI))
                papersInfo = getPapersInfoFromDOIs(DOI, restrict)
                to_download.append(papersInfo)

            num += 1
            i += 1

    if restrict != 0 and to_download:
        if filter_jurnal_file is not None:
            to_download = filterJurnals(to_download, filter_jurnal_file)

        if min_date is not None:
            to_download = filter_min_date(to_download, min_date)

        if num_limit_type is not None and num_limit_type == 0:
            to_download.sort(key=lambda x: int(x.year) if x.year is not None else 0, reverse=True)

        if num_limit_type is not None and num_limit_type == 1:
            to_download.sort(key=lambda x: int(x.cites_num) if x.cites_num is not None else 0, reverse=True)

        downloadPapers(to_download, dwn_dir, num_limit, SciHub_URL)

    Paper.generateReport(to_download, dwn_dir + "result.csv")
    Paper.generateBibtex(to_download, dwn_dir + "bibtex.bib")


def main():
    print(
        """PyPaperBot is a Python tool for downloading scientific papers using Google Scholar, Crossref and SciHub.\nIf you like this project, you can give me a cup of coffee at --> https://www.paypal.com/paypalme/ferru97 <-- :)\n""")

    parser = argparse.ArgumentParser(
        description='PyPaperBot is python tool to search and dwonload scientific papers using Google Scholar, Crossref and SciHub')
    parser.add_argument('--query', type=str, default=None,
                        help='Query to make on Google Scholar or Google Scholar page link')
    parser.add_argument('--doi', type=str, default=None,
                        help='DOI of the paper to download (this option uses only SciHub to download)')
    parser.add_argument('--doi-file', type=str, default=None,
                        help='File .txt containing the list of paper\'s DOIs to download')
    parser.add_argument('--scholar-pages', type=str,
                        help='If given in %%d format, the number of pages to download from the beginning. '
                             'If given in %%d-%%d format, the range of pages (starting from 1) to download (the end is included). '
                             'Each page has a maximum of 10 papers (required for --query)')
    parser.add_argument('--dwn-dir', type=str, help='Directory path in which to save the results')
    parser.add_argument('--min-year', default=None, type=int, help='Minimal publication year of the paper to download')
    parser.add_argument('--max-dwn-year', default=None, type=int,
                        help='Maximum number of papers to download sorted by year')
    parser.add_argument('--max-dwn-cites', default=None, type=int,
                        help='Maximum number of papers to download sorted by number of citations')
    parser.add_argument('--journal-filter', default=None, type=str,
                        help='CSV file path of the journal filter (More info on github)')
    parser.add_argument('--restrict', default=None, type=int, choices=[0, 1],
                        help='0:Download only Bibtex - 1:Down load only papers PDF')
    parser.add_argument('--scihub-mirror', default=None, type=str,
                        help='Mirror for downloading papers from sci-hub. If not set, it is selected automatically')
    parser.add_argument('--scholar-results', default=10, type=int, choices=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
                        help='Downloads the first x results for each scholar page(default/max=10)')
    parser.add_argument('--proxy', nargs='+', default=[],
                        help='Use proxychains, provide a seperated list of proxies to use.Please specify the argument al the end')
    parser.add_argument('--single-proxy', type=str, default=None,
                        help='Use a single proxy. Recommended if using --proxy gives errors')
    parser.add_argument('--mix-file', type=str, default=None,
                        help='File .csv containing the list of paper names and each paper\'s DOIs to download')
    args = parser.parse_args()

    if args.single_proxy is not None:
        os.environ['http_proxy'] = args.single_proxy
        os.environ['HTTP_PROXY'] = args.single_proxy
        os.environ['https_proxy'] = args.single_proxy
        os.environ['HTTPS_PROXY'] = args.single_proxy
        print("Using proxy: ", args.single_proxy)
    else:
        pchain = []
        pchain = args.proxy
        proxy(pchain)

    if args.query is None and args.doi_file is None and args.doi is None and args.mix_file is None:
        print("Error, provide at least one of the following arguments: --query or --file")
        sys.exit()

    if (args.query is not None and args.doi_file is not None) or (args.query is not None and args.doi is not None) or (
            args.doi is not None and args.doi_file is not None):
        print("Error: Only one option between '--query', '--doi-file' and '--doi' can be used")
        sys.exit()

    if args.dwn_dir is None:
        print("Error, provide the directory path in which to save the results")
        sys.exit()

    if args.scholar_results != 10 and args.scholar_pages != 1:
        print("Scholar results best applied along with --scholar-pages=1")

    dwn_dir = args.dwn_dir.replace('\\', '/')
    if dwn_dir[-1] != '/':
        dwn_dir += "/"

    if args.max_dwn_year is not None and args.max_dwn_cites is not None:
        print("Error: Only one option between '--max-dwn-year' and '--max-dwn-cites' can be used ")
        sys.exit()

    if args.query is not None:
        if args.scholar_pages:
            try:
                split = args.scholar_pages.split('-')
                if len(split) == 1:
                    scholar_pages = range(1, int(split[0]) + 1)
                elif len(split) == 2:
                    start_page, end_page = [int(x) for x in split]
                    scholar_pages = range(start_page, end_page + 1)
                else:
                    raise ValueError
            except Exception:
                print(
                    r"Error: Invalid format for --scholar-pages option. Expected: %d or %d-%d, got: " + args.scholar_pages)
                sys.exit()
        else:
            print("Error: with --query provide also --scholar-pages")
            sys.exit()
    else:
        scholar_pages = 0

    DOIs = None
    if args.doi_file is not None:
        DOIs = []
        f = args.doi_file.replace('\\', '/')
        with open(f) as file_in:
            for line in file_in:
                if line[-1] == '\n':
                    DOIs.append(line[:-1])
                else:
                    DOIs.append(line)
    
    if args.mix_file is not None:
        DOIs = []
        f = args.mix_file.replace('\\', '/')
        with open(f) as file_in:
            for line in file_in:
                if line[-1] == '\n':
                    print(line[:-1].split(','))
                    DOIs.append(line[:-1].split(','))
                else:
                    print(line.split(','))
                    DOIs.append(line.split(','))

    if args.doi is not None:
        DOIs = [args.doi]

    max_dwn = None
    max_dwn_type = None
    if args.max_dwn_year is not None:
        max_dwn = args.max_dwn_year
        max_dwn_type = 0
    if args.max_dwn_cites is not None:
        max_dwn = args.max_dwn_cites
        max_dwn_type = 1


    start(args.query, args.scholar_results, scholar_pages, dwn_dir, proxy, args.min_year , max_dwn, max_dwn_type , args.journal_filter, args.restrict, DOIs, args.scihub_mirror)

if __name__ == "__main__":
    main()
    print(
        """\nWork completed!\nIf you like this project, you can offer me a cup of coffee at --> https://www.paypal.com/paypalme/ferru97 <-- :)\n""")
