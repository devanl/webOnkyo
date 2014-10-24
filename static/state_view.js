/**
 * Created by DLippman on 10/09/2014.
 */

function ProgramDescriptionView(model_type)
{
    this.my_model = new model_type();
    this.my_model.load_desc(this);

    this.zones = {};

    this.output_list = $('<ul id="output"></ul>').appendTo( 'body' );
}

ProgramDescriptionView.prototype.load_desc_view = function(data) {
    this.container = $( '<div id="webonkyo-containter"></div>' ).appendTo( 'article#webOnkyo-page' );
    for (var key in data) {
        this.zones[key] = new ZoneView(this.container, key, data[key]);
    }

//    this.update_status({'data':JSON.stringify(['zone3','volume','10'])});
//    this.update_status({'data':JSON.stringify(['zone3','input-selector','CD'])});
};

function ZoneView(parent, zone_name, data) {
    this.wo_name = zone_name;
    this.fields = {};
    this.container = $( '<div class="webonkyo zone-container zone-container-' + zone_name + '"><h2>' + zone_name + '</h2></div>' );
    this.container.appendTo( parent );
    for (var key in data) {
        this.fields[key] = new ControlView(this.container, key, data[key]);
    }
    this.container.data('view_obj', this);
}

function ControlView(parent, control_name, data) {
    this.wo_name = control_name;
    this.type = undefined;

    var action = function() {
        var my_selector = $( this );
        var fqn = ControlView.prototype.fqn(my_selector);

        fqn += '=' + this.value;

        console.log('Click function: ' + fqn);

        var jqxhr = $.getJSON( "command/"+fqn, function() {
          console.log( "success" );
        })
          .fail(function() {
            console.log( "error" );
          })
    };

    if ('type' in data){
        this.type = data['type'];
        if( data['type'] == 'option' ){
            this.container = $('<form class="webonkyo"><fieldset data-role="controlgroup" data-type="horizontal" ' +
                'data-mini="true"></fieldset></form>');

            this.options = {};

            var option_char = 'a';

            for (var key in data.options) {

                var input = $('<input type="radio" name="radio-choice-h-2"\
                  id="radio-choice-h-6' + option_char + '" value="' + key + '"><label\
                  for="radio-choice-h-6' + option_char + '">' + data.options[key] + '</label>');
                input.appendTo(this.container.children());

                $(input[0]).bind("click", action);

                this.options[key] = input;

                option_char = String.fromCharCode(option_char.charCodeAt(0) + 1);

            }
            this.container.appendTo(parent).trigger("create");
        } else if ( data['type'] == 'int' ){
            this.container = $( '<div class="ui-field-contain"></div' ).appendTo(parent);
            this.container = $( '<input type="range" data-mini="true" min="0" max="100" value="50" ' +
                'data-highlight="true" class="webonkyo">' ).appendTo(this.container);
            this.container.bind("slidestop", action);
            this.container.slider();
        }
    }
    this.container.data('view_obj', this);
}

ControlView.prototype.fqn = function(element) {
    if (element.hasClass('webonkyo')) {
        var temp = $(element).data('view_obj');

        if (element.hasClass("zone-container")) {
            return temp.wo_name
        } else {
            return ControlView.prototype.fqn(element.parent()) + '.' + temp.wo_name
        }
    } else {
        return ControlView.prototype.fqn(element.parent())
    }
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
    var data = JSON.parse(message.data)[1];

    var zone = data[0];
    var field = data[1];
    var status = data[2];

    var zone_element =  this.zones[zone];

    // Some fields come back with more than one name
    var field_container = undefined;
    if (field instanceof Array) {
        for (var field_name in field) {
            if (field[field_name] in zone_element.fields) {
                field_container = zone_element.fields[field[field_name]];
            }
        }
    } else {
        field_container = zone_element.fields[field];
    }

    if(field_container != undefined) {
        if(field_container.type == 'option') {
            for (var idx in field_container.options) {
                $( field_container.options[idx][0] ).prop("checked", false).checkboxradio( "refresh" );
            }
            if (status instanceof Array) {
                for (var status_idx in status) {
                    if (status[status_idx] in field_container.options) {
                        $( field_container.options[status[status_idx]][0] ).prop("checked", true).checkboxradio( "refresh" );
                    }
                }
            } else {
                $( field_container.options[status][0] ).prop("checked", true).checkboxradio( "refresh" );
            }
        }else if(field_container.type == 'int') {
            if ( typeof(status) == 'string') {
                status = parseInt('0x' + status);   // Convert hex string to int
            }
            field_container.container.val(status).slider("refresh");
        }
    }
    console.log('Status message completed');
};
