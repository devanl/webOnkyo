/**
 * Created by DLippman on 10/09/2014.
 */

function ProgramDescriptionView(model_type)
{
    this.my_model = new model_type();
    this.my_model.load_desc(this);

    this.output_list = $('<ul id="output"></ul>').appendTo(this.pane.bottom);
}

ProgramDescriptionView.prototype.load_desc_view = function(data) {
    this.container = $( '<div id="webonkyo-containter"></div>' ).appendTo( 'body' );
    for (var key in data) {
        ZoneView(key, data[key]).appendTo( container );
    }
};

function ZoneView(zone_name, data) {
    this.zone = zone_name;
    this.container = $( '<h2 id=zone-container-"' + zone_name + '">' + zone_name + '</h2>' )
    for (var key in data) {
        ControlView(key, data[key]).appendTo( container )
    }
}

function ControlView(control_name, data) {
    this.control = control_name;
    if ('type' in data){
        if( data['type'] == 'option' ){
            this.container = $( '<div class="ui-field-contain"><fieldset data-role="controlgroup" data-type="horizontal" data-mini="true"/></div>' )
            for (var key in data['options']) {
                var input = $( '<input type="radio" name="radio-action" id="' + key + '" value="' + key + '"><label for="' + key + '">' + data['options'][key] + '</label>' )
                input.appendTo( container.next() )
            }
        } else if ( data['type'] == 'int' ){
            this.container = $( '<input type="range" data-mini="true" min="0" max="100" value="50">' )
        }
    }
}

ProgramDescriptionView.prototype.save_desc = function() {
    this.my_model = this.create_model();
    this.my_model.save_desc();
};

ProgramDescriptionView.prototype._stop_desc_callback = function(data) {
    console.log('_stop_desc returned with : ' + data.retval);
    var dialog;
    if(data.retval == 'success') {

    } else {
        dialog = $('<div id="dialog-message" title="Failure Stopping" class="ui-state-error"><p>\
                        <span class="ui-icon ui-icon-alert" style="float:left; margin:0 7px 50px 0;"></span>\
                        Error stopping test!\
                        </p></div>');
        dialog.appendTo($('body'));
        dialog.dialog({
          modal: true,
          buttons: {
            Ok: function() {
              $( this ).dialog( "close" );
            }
          }
        });
    }
};

ProgramDescriptionView.prototype.stop_desc = function() {
    this.my_model.stop_desc(this._stop_desc_callback);
};


ProgramDescriptionView.prototype.update_error = function(message)
{
//    console.log('A status message has arrived!');
    var data = JSON.parse(message.data);

    var dialog = $('<div id="dialog-message" title="Error!"><p>\
    <span class="ui-icon ui-icon-circle-check" style="float:left; margin:0 7px 50px 0;"></span>\
    Error : ' + data.message + '</p></div>');
    dialog.appendTo($('body'));
    dialog.dialog({
      modal: true,
      buttons: {
        Ok: function() {
          $( this ).dialog( "close" );
        }
      }
    });

};

ProgramDescriptionView.prototype.update_status = function(message)
{
//    console.log('A status message has arrived!');
    var data = JSON.parse(message.data);

};
