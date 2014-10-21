/**
 * Created by DLippman on 10/09/2014.
 */

function ProgramDescriptionView(model_type)
{
    this.my_model = new model_type();
    this.my_model.load_desc(this);

    this.output_list = $('<ul id="output"></ul>').appendTo( 'body' );
}

ProgramDescriptionView.prototype.load_desc_view = function(data) {
    this.container = $( '<div id="webonkyo-containter"></div>' ).appendTo( 'article#webOnkyo-page' );
    for (var key in data) {
        var view_element = new ZoneView(this.container, key, data[key]);
    }
};

function ZoneView(parent, zone_name, data) {
    this.wo_name = zone_name;
    this.container = $( '<div class="webonkyo zone-container zone-container-' + zone_name + '"><h2>' + zone_name + '</h2></div>' )
    this.container.appendTo( parent );
    for (var key in data) {
        var view_element = new ControlView(this.container, key, data[key]);
    }
    this.container.data('view_obj', this);
}

function ControlView(parent, control_name, data) {
    this.wo_name = control_name;

    var action = function() {
        var my_selector = $( this );
        var fqn = ControlView.prototype.fqn(my_selector);

        fqn += this.value;

        console.log('Click function: ' + fqn)

        var jqxhr = $.getJSON( "command/"+fqn, function() {
          console.log( "success" );
        })
          .fail(function() {
            console.log( "error" );
          })
    };

    if ('type' in data){
        if( data['type'] == 'option' ){
            this.container = $('<form class="webonkyo"><fieldset data-role="controlgroup" data-type="horizontal" ' +
                'data-mini="true"></fieldset></form>');

            var option_char = 'a';

            for (var key in data.options) {

                var input = $('<input type="radio" name="radio-choice-h-2"\
                  id="radio-choice-h-6' + option_char + '" value="' + key + '"><label\
                  for="radio-choice-h-6' + option_char + '">' + data.options[key] + '</label>');
                input.appendTo(this.container.children());

                $(input[0]).bind("click", action);

                option_char = String.fromCharCode(option_char.charCodeAt(0) + 1);

            }
            this.container.appendTo(parent).trigger("create");
        } else if ( data['type'] == 'int' ){
            this.container = $( '<input type="range" data-mini="true" min="0" max="100" value="50" ' +
                'data-highlight="true" name="slider-0" class="webonkyo" id="slider-0">' ).appendTo(parent);
            this.container.bind("slidestop", action);
            this.container.slider();
        }
    }
    this.container.data('view_obj', this);
}

ControlView.prototype.fqn = function(element) {
    var ret_val = '';
    if (element.hasClass('webonkyo')) {
        var temp = $(element).data('view_obj');
        ret_val = temp.wo_name + '.'
    }

    if (element.hasClass("zone-container")) {
        return ret_val
    } else {
        return ControlView.prototype.fqn(element.parent()) + ret_val
    }
};

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
