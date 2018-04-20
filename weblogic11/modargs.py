import re
from sets import Set
# Variables with dummy values.
domain_name='mydomain'
java_home='/path/to/java/home'
middleware_home='/opt/app/weblogic'
weblogic_home='/opt/app/weblogic/wlserver'
domain_home='/opt/app/weblogic/domains/mydomain'
node_manager_home='/opt/app/weblogic/oracle_common/common/nodemanager'
weblogic_template=weblogic_home + '/common/templates/wls/wls.jar'
admin_server_url = 't3://127.0.0.1:9913'
user_file = "/path/to/userfile"
key_file = "/path/to/keyfile"

#This function takes a list of JVM arguments and converts it to a dictionary of key,value pairs with the dict key being the argument, and the value being a complete copy of the argument broken into key, separator, value
def argdict ( arglist ):
    parsedargdict = {}
    for arg in arglist:
        # Check for args delimited by :
        if ":" in arg:
            #XX options have trailing colons always so that won't do at all.
            if "-XX" in arg:
                # If it's an XX with an =, we'll split at the =, otherwise we'll just add it with no value.
                if "=" in arg:
                    key,value=arg.split("=")
                    parsedargdict[key] = (key,'=',value)
                else:
                    parsedargdict[arg] = None
            # Not an -XX so we can split at : safely. hopefully. You just don't know for sure until you try.
            else:
                key,value=arg.split(":")
                parsedargdict[key] = (key,':',value)
        # Check for args delimited by =
        elif "=" in arg:
            key,value=arg.split("=")
            parsedargdict[key] = (key,'=',value)
        # Check for args with numeric values but no delimiter like our old pal xmx.
        elif re.match(r"(-[a-z]+)([0-9]+[g|m|k])", arg, re.I):
            nondelimited_match = re.match(r"(-[a-z]+)([0-9]+[g|m|k])", arg, re.I)
            if nondelimited_match:
                nond_arg=nondelimited_match.groups()
                parsedargdict[nond_arg[0]] = (nond_arg[0],"",nond_arg[1])
        # I'm out of ideas so we'll just add the arg with a key of "none".
        else:
            parsedargdict[arg] = None
    # Iterate over the current args.  If they exist in the new arg dictionary, add the new arg value.
    return parsedargdict

#this function takes a key value pair and determines if it's a none value.  Returns the key if the value is none, otherwise joins the values.
def flagchecker ( key,value ):
    if value is None:
        argtouse = key
    else:
        argtouse = ("".join(value))
    print(argtouse)
    return argtouse

#This function takes a string of JVM arguments, compares them to the existing arguments on a server, and returns an updated string containing updated vlues for existing args, unchanged arguments from the existing server, and any new args.
def genargs ( newargs, server ):
    try:
        cd('/Servers/' + currentserver)
        currentargs = cmo.getServerStart().getArguments()
        # Create a list of new and existing JVM args
        newarglist = newargs.split()
        currentarglist = currentargs.split()
        # Create some empty dictionaries
        finalargs = []
        argstonuke = []
        # push the new and current args into dictionaries
        newargdict = argdict(newarglist)
        currentargdict = argdict(currentarglist)
        # Look through the new args, and check if they're also in the current arguments.  If they are, stick them in the final arguments with the updated values from the new args.
        for nk,nv in newargdict.iteritems():
            if nk in currentargdict:
                # Check if we have an argument with a key and a value, or just a key.
                newargtoadd = flagchecker(nk,nv)
                finalargs.append(newargtoadd)
                # Pull the current argument out of the current arg dictionary because we're going to wholesale add those later. Should these be pushed to a different dictionary and handled later?  Maybe.
                del currentargdict[nk]
        #Now that we've purged any updated args from the current arguments list, we'll add whatever is left to the final args.  These are unaltered arguments.  Script doesn't support nuking arguments yet.
        for ck,cv in currentargdict.iteritems():
            curargtoadd = flagchecker(ck,cv)
            finalargs.append(curargtoadd)
        # Final args now has any carried over arguments, and updated arguments.  Now we need to add any args that are totally new.  We'll convert finalargs to a dict, then look through the new args for any that didn't get added during the check for updated values.
        finalargdict = argdict(finalargs)
        for nk,nv in newargdict.iteritems():
            if nk not in finalargdict:
                missingarg = flagchecker(nk,nv)
                finalargs.append(missingarg)
        # Now we'll tell the user what we've done.  If you're the cautionous type you could get user verification before proceeding.
        print("You specified these arguments")
        for arg in newargs.split():
            print(arg)
        print("\n")
        print("and the current arguments are")
        for arg in currentargs.split():
            print(arg)
        print("\n")
        finalargset = Set(finalargs) 
        finalstring = " ".join(finalargset)
        print("And the final args I would use for " + currentserver + " are:")
        for arg in finalstring.split():
            print(arg)
    except:
       print 'ERROR';
       dumpStack();
    return finalstring

# This function sets the arguments on a server to a provided value.
def setargs ( mgsvr,jvmargs ):
    print ("Setting JVM args " + jvmargs + " for instance " + mgsvr)
    cd('/Servers')
    cd(mgsvr)
    cd('ServerStart')
    cd(mgsvr)
    cmo.setArguments(jvmargs)
    return
 
# disconnect from  adminserver with a positive note.
def disconnectFromAdminserver():
        print 'Disconnecting from the Admin Server.  Have a nice day.';
        disconnect();

connect(userConfigFile=user_file,userKeyFile=key_file,url=admin_server_url)
edit()
startEdit()
# This iterates through all the servers in the environment.  You probably don't want to do this in real life.
try:
    serverNames = cmo.getServers()
    for server in serverNames:
        currentserver=server.getName()
        # Skip the AdminServer
        if currentserver == 'AdminServer':
            print('skipping Admin Server')
        else:
            #This list of arguments is for demonstration only, some of these I just made up.  This will break if you use it.
            finalargstring = genargs("-Xms8192m -Xmx8192m -XX:MaxPermSize=2048m -Dweblogic.diagnostics.DisableDiagnosticRuntimeControlService=true -DSomeargument -Dweblogic.debug.DebugClusterFragments=true -Dweblogic.debug.DebugClusterSomethingElse=true", currentserver)
            setargs(currentserver, finalargstring)
except:
    print("ERROR")
    dumpStack()
activate(block="true")
disconnect()
