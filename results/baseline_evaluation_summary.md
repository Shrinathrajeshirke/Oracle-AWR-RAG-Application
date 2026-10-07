# AWR RAG Baseline Evaluation Report

## Aggregate Summary

- **Overall Quality:** `0.1098`
- **Completeness:** `0.2361`
- **Specificity:** `0.1167`
- **Structure:** `0.2083`
- **Actionability:** `0.0167`
- **Relevance:** `0.0191`

## Per-Query Results

| # | Question | Quality | Completeness | Specificity | Answer Preview |
| :---: | :--- | :---: | :---: | :---: | :--- |
| 1 | What are the Database Name, Instance Name, and Elapsed Time for this AWR report? | 0.0103 | 0.0000 | 0.0000 | The Database Name is EBSCDB, the Instance Name is ebscdb, and the Elapsed Time f... |
| 2 | What was the total DB Time? | 0.1323 | 0.5000 | 0.1000 | The total DB Time reported in the AWR (Automatic Workload Repository) report is ... |
| 3 | What is the Redo size generated per second and per transaction? | 0.0789 | 0.0000 | 0.1000 | The Redo size generated per second is 25,131.51 bytes, and per transaction is 0.... |
| 4 | How many Logical Reads and Physical Reads occurred per second? | 0.0608 | 0.0000 | 0.1000 | The AWR report provides the following information:  - Logical Reads: 587,289.3 b... |
| 5 | What were the Buffer Cache Hit Ratio and Library Cache Hit Ratio? | 0.1969 | 0.1667 | 0.2000 | The Buffer Cache Hit Ratio and Library Cache Hit Ratio are critical performance ... |
| 6 | How many CPUs and Cores does the host system have? | 0.1081 | 0.1667 | 0.1000 | The host system has 32 CPUs, 16 cores, and 1 socket. These values are obtained f... |
| 7 | What were the top 3 foreground wait events by total wait time (excluding DB CPU)? | 0.2515 | 0.5000 | 0.1000 | The top 3 foreground wait events by total wait time (excluding DB CPU) are:  1. ... |
| 8 | What percentage of total DB time was spent on 'DB CPU'? | 0.1309 | 0.3333 | 0.3000 | From the AWR report, the percentage of total DB time spent on 'DB CPU' was 77.30... |
| 9 | Which Wait Class contributed the most to total wait time after DB CPU, and what was its percentage of DB time? | 0.1304 | 0.3333 | 0.3000 | After DB CPU, the "Concurrency" Wait Class contributed the most to the total wai... |
| 10 | Which SQL_ID had the highest Elapsed Time, and what was its total elapsed time? | 0.1249 | 0.5000 | 0.1000 | The SQL_ID with the highest Elapsed Time can be identified by examining the "SQL... |
| 11 | Identify the top SQL_ID by Buffer Gets. How many gets did it perform? | 0.0354 | 0.1667 | 0.0000 | The SQL statement with the highest number of Buffer Gets is identified by the SQ... |
| 12 | How many executions were there for SQL_ID 0z318y6g3uagc, and what module did it belong to? | 0.0570 | 0.1667 | 0.0000 | For SQL_ID 0z318y6g3uagc, there were 200 executions. It belonged to the module w... |
