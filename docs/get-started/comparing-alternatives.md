(comparint-to-alternatives)=
#COMPARING TO ALTERNATIVES

It is frequently asked how Jina compares to different libraries and frameworks, and we have tried to clarify some of the most common confusions. 

##Compare to MLOps frameworks.

Often community wonders how Jina differs from some MLOps frameworks such as **MLFlow**, **KubeFlow** or **RayWorkflow**. 

The answer to this question is that even when both Jina and these frameworks have these complex Pipelines or **Flows** concepts, they are designed for very different purposes. 

These MLOps frameworks tend to be designed to schedule and operate tasks and jobs targeted for training, hyperparameter tuning, etc … These tasks tend to be slow and generate artifacts from which events are triggered.

On the other hand, Jina is built to build and serve neural search applications built as microservices that communicate through the network in an streaming way. Every microservice (Executor) in a Flow is constantly receiving `docarrays` to be processed in an streaming fashion. 

##Compare to model serving frameworks.

When learning about Executors and the way they are scaled and replicated by Jina, people compare Jina with other Machine Learning model serving frameworks such as **Seldon Core**. 


<<<<<<< HEAD
<<<<<<< HEAD
Seldon is designed to serve and expose single machine learning models of different kinds, classification, regression, etc … Jina, on the other hand is born and built to build end to end neural search applications.
 While these frameworks tend to deploy model artifacts from different ML frameworks in predefined ways, Jina gives all the power to the user by letting them define their own logic with the expressiveness of `DocumentArray` in a Pythonic way.
=======
Seldon is built to serve and expose single machine learning models of different kinds, classification, regression, etc … Jina on the other hand is born and built to build end to end neural search applications.
 While these frameworks tend to deploy model artifacts from different ML frameworks in predefined ways, Jina gives all the power to the user by letting them define their own logic with the expressiveness of `docarray` in a Pythonic way.
>>>>>>> f5d0331707... add comparing to alternatives text
=======
Seldon is designed to serve and expose single machine learning models of different kinds, classification, regression, etc … Jina, on the other hand is born and built to build end to end neural search applications.
 While these frameworks tend to deploy model artifacts from different ML frameworks in predefined ways, Jina gives all the power to the user by letting them define their own logic with the expressiveness of `DocumentArray` in a Pythonic way.
>>>>>>> 24259a999d... docs: good navigation bar

##Compare to Vector Databases.

As part of the Neural Search ecosystem, people often wonders what is the difference between Jina and other Vector Databases.

<<<<<<< HEAD
<<<<<<< HEAD
The main difference is that Jina is **not** a Vector database. 
=======
The main difference is that Jina is not a Vector Database. 
>>>>>>> f5d0331707... add comparing to alternatives text
=======
The main difference is that Jina is **not** a Vector database. 
>>>>>>> 24259a999d... docs: good navigation bar
Jina is a neural search framework to build complete end to end search applications. With the power of **DocumentArray** and **Executors** one can plug any external vector database into a Jina application.
 
 In summary, Jina takes care of the complete pipeline and allows users to integrate their own custom logic and persistence layer. 
