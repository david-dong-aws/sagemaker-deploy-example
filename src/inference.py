import json

"""
SageMaker built-in inference container functions
model_fn, intput_fn, predict_fn, and output_fn are functions that the container
looks for during inference. Definining them here overrides the default behaviors.
See https://docs.aws.amazon.com/sagemaker/latest/dg/adapt-inference-container.html
"""


def model_fn(model_dir):
    """
    Deserialize and return fitted model in memory.
    The output of this function is passed to predict_fn as argument model
    In this model the model loading is handled from the a1_ imports, so nothing 
    is returned here
    """
    
    return None


def input_fn(request_body, request_content_type):
    """
    The model server receives the request data body and the content type,
    and invokes the `input_fn` to process the input
    The output of this function is passed to predict_fn as argument input_data
    Return: a dict
    """
    if request_content_type == "application/json":
        return json.loads(request_body)
    else:
        raise ValueError(
            "Content type {} is not supported.".format(request_content_type)
        )


def predict_fn(input_data, model):
    """
    Model server invokes `predict_fn` on the return value of `input_fn` and `model_fn`

    """

    return "Placeholder prediction: 1234"


def output_fn(predictions, content_type):
    """
    After invoking predict_fn, the model server invokes `output_fn`.
    """
    if content_type == "application/json":
        return predictions
    else:
        raise ValueError("Content type {} is not supported.".format(content_type))
