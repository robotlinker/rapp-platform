import rospy
import sys
import calendar
import time
from datetime import datetime
from os.path import expanduser
from collections import OrderedDict
from app_error_exception import AppError

from rapp_platform_ros_communications.srv import (
  ontologySubSuperClassesOfSrv,
  ontologySubSuperClassesOfSrvRequest,
  ontologySubSuperClassesOfSrvResponse,
  createOntologyAliasSrv,
  createOntologyAliasSrvRequest,
  createOntologyAliasSrvResponse,
  userPerformanceCognitveTestsSrv,
  userPerformanceCognitveTestsSrvRequest,
  userScoreHistoryForAllCategoriesSrv,
  userScoreHistoryForAllCategoriesSrvResponse,
  fetchDataSrv,
  fetchDataSrvRequest,
  fetchDataSrvResponse
  )

from rapp_platform_ros_communications.msg import (  
  StringArrayMsg
  )

class CognitiveExerciseHelperFunctions:
  
  @staticmethod
  ## @brief Gets the user cognitive test performance records for given test type
  # @param username [string] The user's username
  #
  # @return userPerformanceReq [rapp_platform_ros_communications::userPerformanceCognitveTestsSrvRequest::Request&] The user's performance records
  # @exception Exception AppError
  def getUserPerformanceRecordsForTestType(testType,userOntologyAlias):
    serv_topic = rospy.get_param('rapp_knowrob_wrapper_user_performance_cognitve_tests')
    userPerformanceReq=userPerformanceCognitveTestsSrvRequest()
    userPerformanceReq.test_type=testType
    userPerformanceReq.ontology_alias=userOntologyAlias
    knowrob_service = rospy.ServiceProxy(serv_topic, userPerformanceCognitveTestsSrv)
    return knowrob_service(userPerformanceReq)
 

  @staticmethod
  ## @brief Gets the users ontology alias and if it doesnt exist it creates it  
  # @param username [string] The user's username
  #
  # @return ontologyAlias [string] The user's ontology alias
  # @exception Exception AppError
  def getUserOntologyAlias(username):
    serv_topic = rospy.get_param('rapp_knowrob_wrapper_create_ontology_alias')      
    knowrob_service = rospy.ServiceProxy(serv_topic, createOntologyAliasSrv)
    createOntologyAliasReq = createOntologyAliasSrvRequest()
    createOntologyAliasReq.username=username
    createOntologyAliasResponse = knowrob_service(createOntologyAliasReq)
    if(createOntologyAliasResponse.success!=True):
      raise AppError(createOntologyAliasResponse.error, createOntologyAliasResponse.trace)      
    return createOntologyAliasResponse.ontology_alias

  @staticmethod
  ## @brief Queries the ontology and returns the cognitive test types available
  #
  # @return testTypesList [list] The list of the available tests as they were read from the ontology
  # @exception Exception AppError
  def getTestTypesFromOntology():
    serv_topic = rospy.get_param('rapp_knowrob_wrapper_subclasses_of_topic')
    knowrob_service = rospy.ServiceProxy(serv_topic, ontologySubSuperClassesOfSrv)
    testTypesReq = ontologySubSuperClassesOfSrvRequest()
    testTypesReq.ontology_class="CognitiveTests"
    testTypesResponse = knowrob_service(testTypesReq)
    if(testTypesResponse.success!=True):     
      testTypesResponse.trace.append("cannot load test categories from ontology")
      raise AppError(testTypesResponse.error+"cannot load test categories from ontology",testTypesResponse.trace)      
    testTypesList=[]
    for s in testTypesResponse.results:
      tmpList=s.split('#')
      testTypesList.append(tmpList[1])
    return testTypesList

  @staticmethod
  ## @brief Queries the MySQL database through the MySQL wrapper and returns the user's language
  # @param username [string] The username of the user as is in the MySQL database
  # @param languageInSrv [string] The user's language for assigning it to the srv response trace
  #
  # @return languageInSrv [string] The user's language for assigning it to the srv response trace
  # @return userLanguage [string] The user's language
  # @exception Exception AppError
  def getUserLanguage(username,languageInSrv):
    serv_topic = rospy.get_param('rapp_mysql_wrapper_user_fetch_data_topic')	
    knowrob_service = rospy.ServiceProxy(serv_topic, fetchDataSrv)
    fetchDataSrvReq = fetchDataSrvRequest()
    fetchDataSrvReq.req_cols=["language"]
    fetchDataSrvReq.where_data=[StringArrayMsg(s=["username",username])]
    fetchDataSrvResponse = knowrob_service(fetchDataSrvReq)
    if(fetchDataSrvResponse.success.data!=True): 
      raise AppError(fetchDataSrvResponse.trace[0], fetchDataSrvResponse.trace)      
    language=fetchDataSrvResponse.res_data[0].s[0]
    return fetchDataSrvResponse.res_data[0].s[0]

  @staticmethod
  ## @brief Validates the provided test type or selects all test types from ontology if non provided
  # @param testType [string] The provided test type
  # @param validtestTypesList [list] The list of valid test types
  #
  # @return testTypesList [list] The list of testTypes returned
  # @exception Exception AppError
  def determineTestTypeListForReturningScoresOrHistory(testType,validtestTypesList):
    if(not testType==""):
      if(testType not in validtestTypesList):
        error="invalid test type, not contained in ontology subclasses of cognitive test types"
        raise AppError(error,error)        
      testTypesList=[]
      testTypesList.append(req.testType)
    else:
      testTypesList=validtestTypesList
    return testTypesList
  
  @staticmethod  
  ## @brief Organizes the user's performance entries by timestamp
  # @param userPerf [dict] The dictionary containing the user's performance entries
  #
  # @return userPerfOrganizedByTimestamp [OrderedDict] The dictionary containing the user's performance entries organized by timestamp
  def organizeUserPerformanceByTimestamp(userPerf):
    userPerfOrganizedByTimestamp=OrderedDict()
    for i in range(len(userPerf.tests)):
      tlist=[userPerf.tests[i],userPerf.scores[i],userPerf.difficulty[i], userPerf.subtypes[i]]
      userPerfOrganizedByTimestamp[int(userPerf.timestamps[i])]=[tlist]      
    userPerfOrganizedByTimestamp=OrderedDict(sorted(userPerfOrganizedByTimestamp.items(), key=lambda t: t[0], reverse=True)) #Order is descending    
    return userPerfOrganizedByTimestamp
