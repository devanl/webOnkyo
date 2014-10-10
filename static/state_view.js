/**
 * Created by DLippman on 10/09/2014.
 */

function ProgramDescriptionView(model_type)
{
    this.my_model = new model_type();
    this.my_model.load_desc(this);



    this.output_list = $('<ul id="output"></ul>').appendTo(this.pane.bottom);
}

ProgramDescriptionView.prototype.status_bars = function() {
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

ProgramDescriptionView.prototype.load_desc_view = function(desc)
{
    my_self = this;
    this.count_input[0].value = desc['count'];
    desc.states.forEach(function(entry) {
        my_self.add_state_view(entry);
    });
};