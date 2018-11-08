module.exports = function(RED) {
    "use strict";
    var spawn = require('child_process').spawn;
    var fs = require('fs');
    var LCDcommand = __dirname+'/LCD20x4-I2C';
    var debug = false;

    if ( !(1 & parseInt((fs.statSync(LCDcommand).mode & parseInt("777", 8)).toString(8)[0]) )) {
        RED.log.error("File Not Executable",{command:LCDcommand});
        throw "Error : File Not Executable";
    }

    // the magic to make python print stuff immediately
    process.env.PYTHONUNBUFFERED = 1;

    function LCD20x4I2C(n) {
        RED.nodes.createNode(this,n);
        var node = this;
        var statustimeoutfunction;

        if (n.size !== undefined){
            this.lcdsize = n.size;
        }
        else{
            this.lcdsize = false;
        }
        if (n.speed !== undefined){
            this.speed = n.speed;
        }
        else{
            this.speed = false;
        }

        if (isNaN(this.speed)){
            node.status({fill:"red",shape:"dot",text:"Scroll Speed Value NaN"});
            RED.log.error("Scroll Speed Value Error: " + this.speed + " Defaulting to 3");
            this.speed = 3;
        }
        else if (this.speed < 1 || this.speed > 10){
            node.status({fill:"red",shape:"dot",text:"Scroll Speed Value Error"});
            RED.log.error("Scroll Speed Value Error: " + this.speed + " Defaulting to 3");
            this.speed = 3;
        }

        if (this.lcdsize == "20x4"){//|| this.lcdsize == "16x2"){ uncomment to enable 16x2 screens when supported
            node.child = spawn(LCDcommand, ["writelcd",this.lcdsize,this.speed]);
            node.running = true;
            node.status({fill:"green",shape:"dot",text:"OK"});
        }
        else{
            node.running = false;
            node.status({fill:"red",shape:"dot",text:"Screen Size Error"});
            RED.log.error("Screen Size Error");
        }

        node.child.stdout.on('data', function (data) {
            data = data.toString().trim();
            if (data.length > 0) {
                clearTimeout(statustimeoutfunction);

                node.status({fill:"red",shape:"dot",text:data});
                RED.log.error(data);

                statustimeoutfunction = setTimeout(function () {
                    node.status({fill:"green",shape:"dot",text:"OK"});
                }, 300000);
            }
        });

        node.child.stderr.on('data', function (data) {
            if (debug) { node.log("err: "+data+" :"); }
        });

        node.child.on('close', function () {
            node.running = false;
            node.child = null;
            if (debug) { node.log("LCD Node Closed"); }
            if (node.done) {
                node.status({fill:"grey",shape:"ring",text:"Closed"});
                node.done();
            }
            else { node.status({fill:"red",shape:"ring",text:"Stopped"}); }
        });

        node.on("close", function(done) {
            node.status({fill:"grey",shape:"ring",text:"Closed"});
            if (debug) { node.log("LCD Node Closed"); }
            if (node.child !== null) {
                node.done = done;
                node.child.stdin.write("close");
                node.child.kill('SIGKILL');
            }
            else { done(); }
        });

        node.child.on('error', function (err) {
            if (err.errno === "ENOENT") { node.error("Command Not Found"); }
            else if (err.errno === "EACCES") { node.error("Command Not Executable"); }
            else { node.error("Error",{error:err.errno}) }
        });

        this.on('input', function (msg) {
            var objecterror = false;
            var msgerror = false;
            var poserror = false;
            var payload = msg.payload;

            try{
                if (payload.msgs === undefined){
                    node.status({fill:"red",shape:"dot",text:"msgs Value not Defined"});
                    RED.log.error("msgs Value not Defined: " + msg.payload);
                    objecterror = true;
                }
            }
            catch(e){
                node.status({fill:"red",shape:"dot",text:"Input not an Object"});
                RED.log.error("Input not an object: " + msg.payload);
                objecterror = true;
            }

            if (!objecterror){
                if (payload.msgs.length > 4){
                    objecterror = true;
                }
                else if (payload.msgs.length < 4){
                    var condition = 4-payload.msgs.length;
                    var temp = {
                        msg: " "
                    };

                    for(var i = 0; i < condition; i++){
                        if(debug){ RED.log.warn("Line " + String(((i-4)*-1)-1) + " Not Set, Sending Blank Line"); }
                        payload.msgs.push(temp);
                    }
                }

                for(var i = 0; i < 4; i++){
                    if (payload.msgs[i].pos !== undefined){
                        if (isNaN(payload.msgs[i].pos)){
                            node.status({fill:"red",shape:"dot",text:"Message Position Value Error"});
                            RED.log.error("Message Position Value Error: " + payload.msgs[i].pos);
                            poserror = true;
                        }
                        if (payload.msgs[i].pos < 1 || payload.msgs[i].pos > 20){
                            node.status({fill:"red",shape:"dot",text:"Message Position not 1-20"});
                            RED.log.error("Message Position not 1-20: " + payload.msgs[i].pos);
                            poserror = true;
                        }
                    }
                    else{
                        payload.msgs[i].pos = 1;
                    }
                }
            }

            if (!objecterror && !msgerror && !poserror){
                if (node.child !== null) {
                    node.child.stdin.write(JSON.stringify(payload) + "\n");
                }
                node.status({fill:"green",shape:"dot",text:"OK"});
            }
            else{
                RED.log.error("Error Sending Message to LCD - See Error Above");
                var errormsg = '{"msgs": [{"msg": "ERROR","pos": 8},{"msg": "DETECTED","pos": 7}]}';
                node.child.stdin.write(errormsg + "\n");
            }
        });
    }
    RED.nodes.registerType("LCD20x4-I2C",LCD20x4I2C);
};
