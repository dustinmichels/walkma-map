from export import run
from extract import download_and_process_gsheet

if __name__ == "__main__":
    # extract
    download_and_process_gsheet()

    # export
    run()
