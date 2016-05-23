# -*- coding: utf-8 -*-
"""
Created on Tue Oct  6 13:43:58 2015

@author: Wei Zheng
GWID:G31202457
"""

import os
import pymongo as pg
import json
import pulp as pp
import MySQLdb as myDB
import warnings

def getFileNames():
    """
    read json file names
    """
    included_extenstions = ['json' ]
    file_names = [fn for fn in os.listdir(os.getcwd()) 
    if any([fn.endswith(ext) 
    for ext in included_extenstions])] 
    return file_names

def getCollection():
    """
    get LPs collection
    """
    client = pg.MongoClient("localhost:27017")
    db = client["myDB"]
    collection = db['LPs']
    return collection
    
def readAndStore(fns, collection):
    """
    json to mongo
    """
    collection.remove()
    for fn in fns:
        with open(fn,'r') as f:
            LPdata = json.load(f)
            collection.insert(LPdata)

def getAndSolveLP(collection):
    """
    get problems from mongo then solve 
    """
    allObjs = collection.find()
    return [createAndSolveLP(obj) for obj in allObjs] 
    
def createAndSolveLP(LPData):
    """
       Input = JSON object
       Returns = a dictionary with 2 elements
                 The first element is the key value pair of the objective function
                 And the value of the objective function and the second element is a
                 dictionary whose key value pair is the decision variables and their
                 values
                 If this is not to your liking, you can choose to return the data
                 structure of your choice
    """
    if  LPData['objective'] == 'MIN':
        mode = pp.LpMinimize
        objective = "minimum"
    else :
        mode = pp.LpMaximize
        objective = "maximum"
    LHS = LPData["LHS"]
    conditions = LPData["conditions"]
    RHS = LPData["RHS"]
    model = pp.LpProblem(LPData['name'], mode)
    variables = LPData['variables']
    x_d = pp.LpVariable.dict("x_%s", variables,lowBound =0)
    coeffs = dict(zip(variables, LPData['objCoeffs']))
    #set up objective
    model += sum( [coeffs[v] * x_d[v] for v in variables])
    cons_keys = LPData['LHS'].keys()
    #get a list of lp x variables with the order match constraints
    #a dict may not maintain the order of items
    x_l = [x_d[v] for v in variables]
    len_var = len(x_l)
    #add constraint
    for key in cons_keys:
        #conditions as string so use exec 
        exec "model += sum([LHS[key][i] * x_l[i] for i in xrange(len_var)]) " +  conditions[key] + str(RHS[key]) in globals(), locals()
    status = model.solve()
    if pp.LpStatus[status] != "Optimal":
        model_value = "NA"
    else:
        model_value = sum([coeffs[v] * x_d[v].value() for v in variables])
    outputs = {}
    var_values = {v: x_d[v].value() for v in variables}
    outputs["name"] = LPData['name']
    outputs["optimal"] = model_value
    outputs["objective"] = objective
    outputs["var_values"] = var_values
    return outputs
     
    
def writeFile(filename, txt):
    """
    write outputs to a file
    """
    print "Output being sent to: " + filename
    try:
        with open(filename, "w") as f:
            f.write(txt)
            print "Output written to: " + filename
    except Exception, e:
        with open("myerr.txt", "w") as f:
            f.write(str(e))

def write2Mysql(myTable,LPResults):
    con = myDB.connect(host='localhost', user='root', passwd='root')
    cursor = con.cursor()
    warnings.simplefilter("ignore")
    cursor.execute("Create Database if not exists LP;")
    con.select_db("LP")
    #check if table exist
    sql =  "Select count(*) from information_schema.tables where table_name = '" + myTable + "'"
    cursor.execute(sql)
    if cursor.fetchone()[0] == 0:
        sql =  "Create table " + myTable + "(problemName char(20), optimalValue char(20));"  
        cursor.execute(sql)
    else:
        sql =  "Drop table " + myTable + ";"  
        cursor.execute(sql)
        sql =  "Create table " + myTable + "(problemName char(20), optimalValue char(20));"  
        cursor.execute(sql)
    print "Output being sent to: {0} in the LP database".format(myTable) 
    for result in LPResults:
        values = "'{0}','{1:.3f}'".format(result['name'], result['optimal'])
        sql = "Insert into " + myTable + " values(" + values + ");"
        cursor.execute(sql)
    con.commit()
    print "Output written to: {0} in the LP database".format(myTable) 
    
    