# -*- coding: utf-8 -*-
"""
Created on Tue Sep 29 11:28:10 2015

@author: weizheng
GWID: G31202457
The mail file for the program.
"""
import argparse as ag
import A05Module_G31202457 as myModule


def main():
    parser = ag.ArgumentParser()                                                   
    parser.add_argument("-d","--database",dest="outtable", action="store", help="Send the result to a database")
    parser.add_argument("-t","--textfile",dest="outfile", action="store", help="Send the result to a file")                                   
    myArgs = parser.parse_args()
    fns = myModule.getFileNames()
    collection = myModule.getCollection()
    myModule.readAndStore(fns,collection)
    results = myModule.getAndSolveLP(collection)
    lines = ["The optimal value for " + r["name"] + " is " + 
                "{:0.3f}".format(r["optimal"]) for r in results]
    txt = "\n".join(lines)
    print txt       
    if myArgs.outfile:
        myModule.writeFile(myArgs.outfile, txt)
    if myArgs.outtable:
        myModule.write2Mysql(myArgs.outtable, results)
    
if __name__ == "__main__":
    main()