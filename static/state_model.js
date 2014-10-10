/**
 * Created by DLippman on 9/22/2014.
 */

function ProgramDescriptionModel()
{
    this.my_desc = {states: [], count: 1}
}

ProgramDescriptionModel.prototype.load_desc = function(view_obj) {
    var my_obj = this;
    $.getJSON($SCRIPT_ROOT + '/_load_desc', function (data) {
        my_obj.my_desc = data;
        console.log("Got description");
    })
        .done(function () {
            console.log("Loaded description successfully");
        })
        .fail(function () {
            console.log("Failed to load description");
        })
        .always(function () {
            view_obj.load_desc_view(my_obj.my_desc);
            console.log("_load_desc complete");
        });
};

ProgramDescriptionModel.prototype.save_desc = function() {
    this._put_with_response($SCRIPT_ROOT + '/_save_desc',
                            this.my_desc,
                            function(data){
                                console.log('_save_desc returned with : ' + data.retval)
                                if(data.retval == 'success') {
                                    var dialog = $('<div id="dialog-message" title="Saved"><p>\
    <span class="ui-icon ui-icon-circle-check" style="float:left; margin:0 7px 50px 0;"></span>\
    Description saved successfully.\
  </p></div>');
                                    dialog.appendTo($('body'))
                                    dialog.dialog({
                                      modal: true,
                                      buttons: {
                                        Ok: function() {
                                          $( this ).dialog( "close" );
                                        }
                                      }
                                    });
                                }
                            })
};

ProgramDescriptionModel.prototype.exec_desc = function() {
    this._put_with_response($SCRIPT_ROOT + '/_run_desc',
                            this.my_desc,
                            function(data){
                                console.log('_run_desc returned with : ' + data.retval)
                            })
};

ProgramDescriptionModel.prototype._put_with_response = function(url, data, callback) {
    $.ajax({
      url: url,
      data: JSON.stringify(data),
      success: function(data) {
          console.log( "_put_with_response returned" );
          callback(data);
      },
      type: 'PUT',
      dataType: "json",
      contentType: 'application/json'})
    .done(function() {
        console.log( "_put_with_response returned success" );
    })
    .fail(function() {
        console.log( "_put_with_response Failed " );
    })
    .always(function() {
        console.log( "_put_with_response complete" );
    });
  return false;
};

ProgramDescriptionModel.prototype.stop_desc = function(callback) {
    $.ajax({
      url: '/_stop_desc',
      success: function(data) {
          console.log( "stop_desc returned" );
          callback(data);
      },
      dataType: "json",
      type: 'GET'})
    .done(function() {
        console.log( "stop_desc returned success" );
    })
    .fail(function() {
        console.log( "stop_desc Failed " );
    })
    .always(function() {
        console.log( "stop_desc complete" );
    });
  return false;
};
