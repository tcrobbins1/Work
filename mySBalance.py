#!/bin/python

import subprocess  # Needed for running scontrol
import getpass  # Needed for getting username
import re  # Needed for matching and subbing
import argparse  # Needed for processing input commands
from prettytable import PrettyTable  # Needed for formatting output
from pint import UnitRegistry  # Needed for easy unit conversions
ureg = UnitRegistry()  # Setting up unit conversions

# All string data passed to functions represented by x or d variables are split into arrays before being passed
# This makes it easier to format


def parse_data(u, d):  # Parses the data so that it can be printed in a somewhat appealing manner later
                    # This is extremely important for the main loops of the program
                    # (d: the data to be parsed)
    # Formatting the original values
    dataString0 = re.sub('NumUsers=', '', d[0])
    dataString1 = re.sub('Account=', '', d[1])
    if d[2] == 'UserName=':
        dataString2 = re.sub(r'^UserName=$', dataString0, d[2])  # This line is required for groups
    else:
        dataString2 = re.sub('UserName=', '', d[2])     # This line is for individual users
    dataString2 = re.sub(r'\(.*\)', '', dataString2)
    dataString3 = re.sub('ParentAccount=', '', d[3])
    if dataString3 == '':
        dataString3 = ' . '
    dataString3 = re.sub(r'\(.*\)', '', dataString3)
    dataString4 = re.sub('GrpTRESMins=', '', d[4])

    # Formatting pieces of the original and getting the important bits
    gtm = dataString4.split(',')
    for i in [0, 1, 3, 4]:
        gtm[i] = re.sub(r'^.*=', '', gtm[i])
        gtm[i] = re.sub(r'\)', '', gtm[i])
    cpu = gtm[0].split('(')
    if cpu[0] == "N":
        cpu[0] = '0'
    for j in [1, 3, 4]:
        gtm[j] = re.sub(r'N\(', '', gtm[j])
    rList = [dataString1, dataString2, dataString3, cpu[0], cpu[1], gtm[1], gtm[3], gtm[4]]
    for k in range(3, 8):  # Setting up units/formatting
            rList[k] = int(rList[k]) * ureg.minute
            if u == 'h':
                rList[k].ito(ureg.hour)
            rList[k] = str(int(rList[k].magnitude))
    return(rList)


def print_data(u, p, v, group, notgroup):  # The final act of the program required for any data to appear
            # (u: the units either 'm' or 'h'; nz: the boolean if skipping inactive users;
            #  p: the boolean if printing parsed data; v: the boolean if printing verbose data;
            #  group: an array containing all the groups; notgroup: an array containing individual users)
    if (p):  # <-p>
        if(v):  # <-v>
            print('Account,User/NumUsers,Parent,CPU Allocation(%s),CPU User(%s),Memory Used(%s),Node Used(%s),GPU Used(%s)' % (u, u, u, u, u))
            for i in group:
                pStr = ','.join(str(k) for k in i)
                print(pStr)
            for j in notgroup:
                pStr2 = ','.join(str(l) for l in j)
                print(pStr2)
        else:
            print('Account,User/NumUsers,Allocation(%s),Used(%s)' % (u, u))
            for i in group:
                print(i[0] + "," + i[1] + "," + i[3] + "," + i[4])
            for j in notgroup:
                print(j[0] + "," + j[1] + "," + j[3] + "," + j[4])
    else:  # Default
        dataTable = PrettyTable()
        if (v):  # <-v>
            dataTable2 = PrettyTable()
            headers = ['Account', 'User/NumUsers', 'Parent', 'CPU Allocation(', 'CPU User(', 'Memory Used(', 'Node Used(', 'GPU Used(']
            for k in range(3, 8):
                headers[k] = headers[k] + u + ')'
            dataTable.field_names = headers
            dataTable2.field_names = headers
            for i in group:
                dataTable.add_row(i)
            for j in notgroup:
                dataTable2.add_row(j)
            dataTable.align = 'r'
            print(dataTable)
            dataTable2.align = 'r'
            print(dataTable2)
        else:   # Default
            headers = 'Account User/NumUsers Allocation(%s) Used(%s)' % (u, u)
            dataTable.field_names = headers.split()
            for i in group:
                dataTable.add_row([i[0], i[1], i[3], i[4]])
            for j in notgroup:
                dataTable.add_row([j[0], j[1], j[3], j[4]])
            dataTable.align = 'r'
            print(dataTable)


# Setting up ArgParse
parser = argparse.ArgumentParser(description="Print account balances.", epilog="asterisk indicates default account")
parser.add_argument('-f', '--full', help="show multiple allocations if user has more than 1", action='store_true')
parser.add_argument('-m', '--minute', help="for minute format (hour format by default)", action='store_const', const='m', default='h')
parser.add_argument('-n', '--nonzero', help="avoid nonzero using users", action='store_true')
parser.add_argument('-a', '--all', help="display all usage", action='store_true')
parser.add_argument('-p', '--parse', help="parsible format", action='store_true')
parser.add_argument('-v', '--verbose', help="verbose usage info", action='store_true')
parser.add_argument('-u', '--user', nargs=1, help="show values for listed user")
args = parser.parse_args()

# Creates a list from the scontrol command that contains user data
scontrolarray = []
sproc1 = subprocess.Popen(['scontrol', 'show', 'cache', '-o'], stdout=subprocess.PIPE)
output1 = sproc1.communicate()[0]
output1 = output1.decode("utf-8")
for line in output1.splitlines():
    if 'marcc' in line:
        scontrolarray.append(line.split()[1] + " " + line.split()[2] + " " + line.split()[7] + " " + line.split()[14])

# Identifying a specific user
try:
    u = args.user[0]
except TypeError:
    u = getpass.getuser()

userarray = []  # The list of important users that lead relevant groups
if (args.full):  # <-f>
    for line in output1.splitlines():  # Filling the userarray with all relevant important user info
        if 'marcc' in line:
            if u in line.split()[2]:
                printstr = line.split()[1] + " " + line.split()[2] + " " + line.split()[14]
                printstr = re.sub(r'^.*Account=', '', printstr)
                printstr = re.sub(r' UserName=', ' ', printstr)
                printstr = re.sub(r'GrpTRESMins=cpu=', ' ', printstr)
                printstr = re.sub(r',mem.*$', '', printstr)
                printstr = re.sub(r'\(.*N\(', '', printstr)
                printstr = re.sub(r'\)', '', printstr)
                userarray.append(printstr.split()[0])
    sproc2 = subprocess.Popen(['scontrol', 'show', 'cache'], stdout=subprocess.PIPE)
    output2 = sproc2.communicate()[0].decode("utf-8")
    for line in output2.splitlines():
        if 'DefAccount' in line:
            if u in line.split()[0]:
                piline = line.split()[1]
                piline = re.sub(r'DefAccount=', '', piline)
                default_pi = piline  # Important user to get identifed with *
else:  # Default
    sproc2 = subprocess.Popen(['scontrol', 'show', 'cache'], stdout=subprocess.PIPE)
    output2 = sproc2.communicate()[0].decode("utf-8")
    for line in output2.splitlines():
        if 'DefAccount' in line:
            if u in line.split()[0]:
                printstr = re.sub(r'DefAccount=', '', line.split()[1])
                userarray.append(printstr)

if (args.all):  # <-a>
    userarray.append('')

groupsarray = []  # The list containing all relevant group info
notgroupsarray = []  # The list containging all relevant individual user info
for pi in userarray:
    garray = []   # Group list for current pi
    ngarray = []  # Individual list for current pi
    numusers4pi = 0
    for i in scontrolarray:
        testStr1 = 'Account=' + pi
        testStr2 = 'Account=' + pi + ' '
        if (args.all):  # <-a>
            if testStr1 in i:
                if 'GrpTRESMins=cpu=N' not in i:  # Finding groups
                    garray.append(i)
                else:  # Finding users
                    ngarray.append(i)
                    numusers4pi = numusers4pi + 1
        else:
            if testStr2 in i:
                if 'GrpTRESMins=cpu=N' not in i:  # Finding groups
                    garray.append(i)
                else:  # Finding users
                    ngarray.append(i)
                    numusers4pi = numusers4pi + 1
    for i in garray:
        parsed = 'NumUsers=' + str(numusers4pi) + ' ' + i
        parsed = parse_data(args.minute, parsed.split())
        try:  # Adding * to the group leaders
            parsed[0] = re.sub(r'^%s' % default_pi, '%s*' % default_pi, parsed[0])
        except NameError:
            parsed[0] = re.sub(r'^%s' % '', '%s*' % '', parsed[0])
        if args.nonzero:
            if parsed[4] != '0':
                groupsarray.append(parsed)
        else:
            groupsarray.append(parsed)
    for i in ngarray:  # Adding all individuals for current pi to the larger individual list
        parseStr = 'NumUsers=' + str(numusers4pi) + ' ' + i
        parseStr = parse_data(args.minute, parseStr.split())
        if args.nonzero:
            if parseStr[4] != '0':
                notgroupsarray.append(parseStr)
        else:
            notgroupsarray.append(parseStr)
print_data(args.minute, args.parse, args.verbose, groupsarray, notgroupsarray)
