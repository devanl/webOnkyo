/**
 * Created by DLippman on 10/09/2014.
 */

function ProgramDescriptionViewMobile(model_type)
{
    this.my_model = new model_type();
    this.my_model.load_desc(this);

    this.output_list = $('<ul id="output"></ul>').appendTo(this.pane.bottom);
}
