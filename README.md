# maltindex

Mal Tindex is an Open Source tool for indexing binaries and help attributing malware campaigns. It was first presented in the EuskalHack 2017 conference, in Donostia (Basque Country). Both Linux, Windows and MacOSX should be supported targets but actual indexing has been only tested in Linux.

## How it works?

It uses (for now) IDA and Diaphora to export to a database a set of signatures for each function found in each binary indexed. Then, the most "rare" functions are stored in various tables and these are used to find "rare" coincidences between malware samples that, perhaps, can be useful in order to attribute actors and malware campaigns.

## How to use it

First of all, you need a Diaphora supported version of IDA (6.8, 6.9 and 6.95) and Python. Once you have all the requirements, you will need to create a *.cfg file to specify the database data (for this first proof-of-concept, there is only support yet for SQLite, but I will add support "soon" for any database supported by web.py). The *.cfg file has the following form:

```
########################################################################
# Example configuration for SQLite3
########################################################################
[database]
dbn=sqlite
# Database name
db=/path/to/your/to/be/created/database/db_name.sqlite
```

Once you have your *.cfg file created, you can run the following commands:

```
$ export DIAPHORA_DB_CONFIG=/path/to/cfg
$ diaphora_index_batch.py /dir/where/ida/is/installed samples_dir
```

It will then find every single executable binary in all directories, recursively, and launch the appropriate IDA program (i.e., idaq or idaq64), and index every binary. After all the binaries are indexed and all tables populated, you can then use the command line tool "malindex.py" to analyse your dataset:

```
$ maltindex.py <database path>
MalTindex> match MD5
(...it will show all matches in the dataset for functions found in the binary with that specific MD5...)
MalTindex> match MD5_1 MD5_2
(...it will show all matches between both MD5s...)
MalTindex> unique MD5
(...it will show unique rare matches for the given MD5, if any...)
```

And that's it! Remember that your dataset must be significantly big in order to get significant results. According to some friends, the minimum required number of binaries (both goodware and malware) is around 1 million samples.

