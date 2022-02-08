#Comparing to alternatives

People often ask how Jina compares to different libraries and frameworks, and here we clarify some of the most common confusions. 

## Compared to MLOps frameworks

Often community wonders how Jina differs from some MLOps frameworks such as **MLFlow**, **KubeFlow** or **RayWorkflow**. 

Even when both Jina and these frameworks have these complex Pipelines or **Flows** concepts, they are designed for very different purposes. 

These MLOps frameworks tend to be designed to schedule and operate tasks and jobs targeted for training, hyperparameter tuning, etc … These tasks tend to be slow and generate artifacts from which events are triggered.

On the other hand, Jina is built to build and serve neural search applications built as microservices that communicate through the network in an streaming way. Every microservice (Executor) in a Flow is constantly receiving `docarrays` to be processed in an streaming fashion. 

##Compare to model serving frameworks

When learning about Executors and the way they are scaled and replicated by Jina, people compare Jina with other Machine Learning model serving frameworks such as **Seldon Core**. 

Seldon is designed to serve and expose single machine learning models of different kinds, classification, regression, etc … Jina, on the other hand, is built for end-to-end neural search applications.
 While these frameworks tend to deploy model artifacts from different ML frameworks in predefined ways, Jina gives all the power to the user by letting them define their own logic with the expressiveness of `DocumentArray` in a Pythonic way.

##Compare to Vector databases

As part of the Neural Search ecosystem, people often wonder about the difference between Jina and other Vector Databases.

The main difference is that Jina is **not** a Vector database. 

Jina is a neural search framework to build complete end to end search applications. With the power of **DocumentArray** and **Executors** one can plug any external vector database into a Jina application.
 
 In summary, Jina takes care of the complete pipeline and allows users to integrate their own custom logic and persistence layer. 
