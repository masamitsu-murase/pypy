

// we should put the imports here.
import mx.controls.Button;


import py.*;
import py.__consts_0;
//import py.f.DictIter;



// starts hand written code
var MALLOC_ZERO_FILLED = 0;

var print = trace;




Function.prototype.method = function (name, func) {
    this.prototype[name] = func;
    return this;
};


import flash.net.*;
public function localFlexTrace ( text:String ):void {
    var myUrl:URLRequest = new URLRequest("javascript:console.log('" + text + "');void(0);");
    sendToURL(myUrl);
}

function __flash_main() {

    localFlexTrace("Starting...");


    try {
        py.__load_consts_flex()
    } catch (exc) {
        __consts_0.flexTrace("consts error");
        __consts_0.flexTrace(String(exc));
    }
    try {
        flash_main(1)
    } catch (exc) {
        __consts_0.flexTrace("flash_main error");
        __consts_0.flexTrace(String(exc));
        __consts_0.flexTrace(String(exc.message));
        __consts_0.flexTrace(exc.getStackTrace());
        
    }
    __consts_0.flexTrace("Exit");

}



// ends hand written code

