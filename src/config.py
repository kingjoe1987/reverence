"""Interface to bulkdata

- loads and prepares the bulkdata for use (on demand)
- provides container classes for record and row data.
- provides interface to the database tables

Copyright (c) 2003-2011 Jamie "Entity" van den Berge <jamie@hlekkir.com>

This code is free software; you can redistribute it and/or modify
it under the terms of the BSD license (see the file LICENSE.txt
included with the distribution).

Parts of code inspired by or based on EVE Online, with permission from CCP.
"""

# TODO:
# - multi language support :)

import time
import sys

from . import _blue as blue
from . import const, util, dbutil

_urga = util.Row.__getattr__


class RecordsetIterator(object):
	def next(self):
		return self.rowset.rowclass(self.rowset.header, self.iter.next(), self.rowset.cfg)


class Recordset(object):
	def __init__(self, rowclass, keycolumn, cfgInstance=None):
		self.rowclass = rowclass
		self.keycolumn = keycolumn
		self.header = {}
		self.data = {}
		self.cfg = cfgInstance

	def Get(self, *args):
		return self.rowclass(self.header, self.data.get(*args), self.cfg)

	def GetIfExists(self, *args):
		return self.rowclass(self.header, self.data.get(*args), self.cfg)

	def __iter__(self):
		it = RecordsetIterator()
		it.rowset = self
		it.iter = self.data.itervalues()
		return it

	def __contains__(self, key):
		return key in self.data


class ItemsRecordset(Recordset):
	pass



class Record(object):
	def Get(self, *args):
		return self.__dict__.get(*args)

	def Update(self, dict):
		if self.__primary__ in dict:
			raise ValueError, "Cannot update primary key '%s' of record" % self.__primary__

		for k in dict.iterkeys():
			if k not in self.__fields__:
				raise IndexError, "Record has no field '%s'" % k

		self.__dict__.update(dict)

class OwnerRecord(Record):
	__primary__ = "ownerID"
	__fields__ = ['ownerID', 'ownerName', 'typeID', 'allianceID', 'corpID', 'role', 'corpRole']

	def __init__(self, ownerID, dict=None):
		self.ownerID = ownerID
		self.ownerName = None
		if dict:
			self.Update(dict)

	def __getattr__(self, attr):
		if attr == "name":
			attr = "ownerName"
		return Record.__getattr__(self, attr)

	def __repr__(self):
		return "<OwnerRecord %s: '%s'>" % (self.ownerID, self.ownerName)


class Billtype(util.Row):
	__guid__ = 'cfg.Billtype'

	def __getattr__(self, name):
		value = _urga(self, name)
#		if name == 'billTypeName':
#			value = Tr(value, 'dbo.actBillTypes.billTypeName', self.billTypeID)
		return value

	def __str__(self):
		return 'Billtype ID: %d' % self.billTypeID


class InvType(util.Row):
	__guid__ = "sys.InvType"

	def Group(self):
		return (self.cfg or cfg).invgroups.Get(self.groupID)

	def Graphic(self):
		if self.graphicID is not None:
			return (self.cfg or cfg).evegraphics.Get(self.graphicID)
		else:
			return None

	def __getattr__(self, attr):
		if attr == "name":
			return _urga(self, "typeName")
		return _urga(self, attr)

	# ---- custom additions ----

	def GetRequiredSkills(self):
		return (self.cfg or cfg).GetRequiredSkills(self.typeID)

	def GetTypeAttrDict(self):
		return (self.cfg or cfg).GetTypeAttrDict(self.typeID)

	def GetTypeAttribute(self, attributeID, defaultValue=None):
		return (self.cfg or cfg).GetTypeAttribute(self.typeID, attributeID, defaultValue)

	def GetTypeAttribute2(self, attributeID):
		return (self.cfg or cfg).GetTypeAttribute2(self.typeID, attributeID)


class InvGroup(util.Row):
	__guid__ = "sys.InvGroup"

	def Category(self):
		return (self.cfg or cfg).invcategories.Get(self.categoryID)

	def __getattr__(self, attr):
		if attr == "name":
			return _urga(self, "groupName")
		if attr == "id":
			return _urga(self, "groupID")
		return _urga(self, attr)


class InvCategory(util.Row):
	__guid__ = "sys.InvCategory"

	def __getattr__(self, attr):
		if attr == "name":
			return _urga(self, "categoryName")
		if attr == "id":
			return _urga(self, "categoryID")
		return _urga(self, attr)

	def IsHardware(self):
		return self.categoryID == const.categoryModule


class InvMetaGroup(util.Row):
	def __getattr__(self, name):
		if name == "_metaGroupName":
			return _urga(self, "metaGroupName")

		if name == "name":
			name = "metaGroupName"

		value = _urga(self, name)
#		if name == "metaGroupName":
#			return self.cfg.Tr(value, "inventory.metaGroups.metaGroupName", self.dataID)
		return value


class DgmAttribute(util.Row):
	def __getattr__(self, name):
		value = _urga(self, name)
#		if name == "displayName":
#			return self.cfg.Tr(value, "dogma.attributes.displayName", self.dataID)
		return value


class DgmEffect(util.Row):
	def __getattr__(self, name):
		value = _urga(self, name)
#		if name == "displayName":
#			return self.cfg.Tr(value, "dogma.effects.displayName", self.dataID)
#		if name == "description":
#			return self.cfg.Tr(value, "dogma.effects.description", self.dataID)
		return value


class EveGraphics(util.Row):
	def __getattr__(self, name):
		if name == "name" or name == "description":
			if "icon" in row.header:
				# Pre-tyrannis.
				return self.icon
			return self.description
		else:
			return _urga(self, name)

	def __str__(self):
		return "EveGraphic ID: %d, \"%s\"" % (self.graphicID, self.icon)


class EveOwners(util.Row):
	def __getattr__(self, name):
		if name == "name" or name == "description":
			name = "ownerName"
		elif name == "groupID":
			return self.cfg.invtypes.Get(self.typeID).groupID

		value = _urga(self, name)
#		if name == "ownerName" and IsSystemOrNPC(self.ownerID):
#			return self.cfg.Tr(value, "dbo.eveNames.itemName", self.ownerID)
		return value


	def __str__(self):
		return "EveOwner ID: %d, \"%s\"" % (self.ownerID, self.ownerName)

	def Type(self):
		return self.cfg.invtypes.Get(self.typeID)

	def Group(self):
		return self.cfg.invgroups.Get(self.groupID)


class EveLocations(util.Row):
	__guid__ = "dbrow.Location"

	def __getattr__(self, name):
		if name == "name" or name == "description":
			name = "locationName"
		value = _urga(self, name)
		return value

	def __str__(self):
		return "EveLocation ID: %d, \"%s\"" % (self.locationID, self.locationName)

#	def Station(self):
#		return self.cfg.GetSvc("stationSvc").GetStation(self.id)



class RamCompletedStatus(util.Row):
	def __getattr__(self, name):
		if name == "name":
			name = "completedStatusName"
		elif name == "completedStatusID" and self.cfg.protocol >= 276:
			name = "completedStatus"

		value = _urga(self, name)
#		if name == "completedStatusName":
#			return self.cfg.Tr(value, "dbo.ramCompletedStatuses.completedStatusText", self.completedStatusID)
#		elif name == "description":
#			return self.cfg.Tr(value, "dbo.ramCompletedStatuses.description", self.completedStatusID)
		return value

	def __str__(self):
		try:
			return "RamCompletedStatus ID: %d, \"%s\"" % (self.completedStatusID, self.completedStatusName)
		except:
			sys.exc_clear()
			return "RamCompletedStatus containing crappy data"


class RamActivity(util.Row):
	def __getattr__(self, name):
    
		if name == "name":
			name = "activityName"
    
		value = _urga(self, name)
#		if name == "activityName":
#			return self.cfg.Tr(value, "dbo.ramActivities.activityName", self.activityID)
#		elif name == "description":
#			return self.cfg.Tr(value, "dbo.ramActivities.description", self.activityID)
		return value

	def __str__(self):
		try:
			return "RamActivity ID: %d, \"%s\"" % (self.activityID, self.activityName)
		except:
			sys.exc_clear()
			return "RamActivity containing crappy data"


class RamDetail(util.Row):
	def __getattr__(self, name):
   		if name == "activityID":
			return self.cfg.ramaltypes.Get(self.assemblyLineTypeID).activityID
   		value = _urga(self, name)
		return value


class MapCelestialDescription(util.Row):
	def __getattr__(self, name):

		# this attribute name changed in protocol 276
		if name == "celestialID" and self.cfg.protocol >= 276:
			name = "itemID"

		value = _urga(self, name)
#		if name == "description":
#			return self.cfg.Tr(value, "dbo.mapCelestialDescriptions.description", self.celestialID)
		return value

	def __str__(self):
		return "MapCelestialDescriptions ID: %d" % (self.celestialID)



class CrpTickerNames(util.Row):
	def __getattr__(self, name):
		if name == "name" or name == "description":
			return self.tickerName
		else:
			return _urga(self, name)

	def __str__(self):
		return "CorpTicker ID: %d, \"%s\"" % (self.corporationID, self.tickerName)


class AllShortNames(util.Row):
	def __getattr__(self, name):
		if name == "name" or name == "description":
			return self.shortName
		else:
			return _urga(self, name)

	def __str__(self):
		return "AllianceShortName ID: %d, \"%s\"" % (self.allianceID, self.shortName)


class Certificate(util.Row):
	def __getattr__(self, name):
		value = _urga(self, name)
#		if name == "description":
#			return self.cfg.Tr(value, "cert.certificates.description", self.dataID)
		return value

	def __str__(self):
		return "Certificate ID: %d" % (self.certificateID)


class Schematic(util.Row):
	__guid__ = 'cfg.Schematic'

	def __getattr__(self, name):
		value = _urga(self, name)
#		if name == 'schematicName':
#			value = self.cfg.Tr(value, 'planet.schematics.schematicName', self.dataID)
		return value

	def __str__(self):
		return 'Schematic: %s (%d)' % (self.schematicName, self.schematicID)

	def __cmp__(self, other):
		if type(other) == int:
			return int.__cmp__(self.schematicID, other)
		else:
			return util.Row.__cmp__(self, other)


# Warning: Code below may accidentally your whole brain.

class _memoize(object):
	# This class is a getter. On attribute access, it will call the method it
	# decorates and replace the attribute value (which is the getter instance)
	# with the value returned by that method. Used to implement the
	# load-on-access mechanism 

	__slots__ = ["method"]

	def __init__(self, func):
		self.method = func

	def __get__(self, obj, type=None):
		if obj is None:
			# class attribute (descriptor itself)
			return self
		else:
			# instance attribute (replaced by value)
			value = self.method(obj)
			setattr(obj, self.method.func_name, value)
			return value


def _loader(attrName):
	# Creates a closure used as a method in Config class (to be decorated with
	# _memoize) that loads a specific bulkdata table.
	def method(self):
		ver, rem, tableName, storageClass, rowClass, primaryKey, bulkID = self._tables[attrName]
#		if self.cache.machoVersion < ver:
#			raise RuntimeError("%s table requires machoNet version %d, cache is version %d." % (tableName, ver, self.cache.machoVersion))
		return self._loadbulkdata(tableName=(tableName or attrName), storageClass=storageClass, rowClass=rowClass, primaryKey=primaryKey, bulkID=bulkID)
	method.func_name = attrName
	return method


class _tablemgr(type):
	# Creates decorated methods in the Config class that handle loading of
	# bulkdata tables on accessing the attributes those methods are bound as.
	# Note: tables that require non-standard handling will need methods for
	# that (decorated with @_memoize) in Config class.

	def __init__(cls, name, bases, dict):
		type.__init__(cls, name, bases, dict)
		for attrName, x in cls.__tables__:
			if hasattr(cls, attrName):
				# specialized loader method exists.
				continue
			setattr(cls, attrName, _memoize(_loader(attrName)))


class Config(object):
	__metaclass__ = _tablemgr

	"""Interface to bulkdata.

	EVE's database is available as attributes of instances of this class.
    Tables are transparently loaded from bulkdata/cache upon accessing such an
    attribute. Because this automatic loading scheme is NOT thread-safe, the
    prime() method should be called prior to allowing other threads access to
    the instance.
    """

	__containercategories__ = (
		const.categoryStation,
		const.categoryShip,
		const.categoryTrading,
		const.categoryStructure,
		)

	__containergroups__ = (
		const.groupCargoContainer,
		const.groupSecureCargoContainer,
		const.groupAuditLogSecureContainer,
		const.groupFreightContainer,
		const.groupConstellation,
		const.groupRegion,
		const.groupSolarSystem,
		const.groupMissionContainer,            
		)

	__chargecompatiblegroups__ = (
		const.groupFrequencyMiningLaser,
		const.groupEnergyWeapon,
		const.groupProjectileWeapon,
		const.groupMissileLauncher,
		const.groupCapacitorBooster,
		const.groupHybridWeapon,
		const.groupScanProbeLauncher,
		const.groupComputerInterfaceNode,
		const.groupMissileLauncherBomb,
		const.groupMissileLauncherCruise,
		const.groupMissileLauncherDefender,
		const.groupMissileLauncherAssault,
		const.groupMissileLauncherSiege,
		const.groupMissileLauncherHeavy,
		const.groupMissileLauncherHeavyAssault,
		const.groupMissileLauncherRocket,
		const.groupMissileLauncherStandard,
		const.groupMissileLauncherCitadel,
		const.groupMissileLauncherSnowball,
		const.groupBubbleProbeLauncher,
		const.groupSensorBooster,
		const.groupRemoteSensorBooster,
		const.groupRemoteSensorDamper,
		const.groupTrackingComputer,
		const.groupTrackingDisruptor,
		const.groupTrackingLink,
		const.groupWarpDisruptFieldGenerator,
		)

	__containerVolumes__ = {
		const.groupAssaultShip: 2500.0,
		const.groupBattlecruiser: 15000.0,
		const.groupBattleship: 50000.0,
		const.groupBlackOps: 50000.0,
		const.groupCapitalIndustrialShip: 1000000.0,
		const.groupCapsule: 500.0,
		const.groupCarrier: 1000000.0,
		const.groupCombatReconShip: 10000.0,
		const.groupCommandShip: 15000.0,
		const.groupCovertOps: 2500.0,
		const.groupCruiser: 10000.0,
		const.groupStrategicCruiser: 10000.0,
		const.groupDestroyer: 5000.0,
		const.groupDreadnought: 1000000.0,
		const.groupElectronicAttackShips: 2500.0,
		const.groupEliteBattleship: 50000.0,
		const.groupExhumer: 3750.0,
		const.groupForceReconShip: 10000.0,
		const.groupFreighter: 1000000.0,
		const.groupFrigate: 2500.0,
		const.groupHeavyAssaultShip: 10000.0,
		const.groupHeavyInterdictors: 10000.0,
		const.groupIndustrial: 20000.0,
		const.groupIndustrialCommandShip: 500000.0,
		const.groupInterceptor: 2500.0,
		const.groupInterdictor: 5000.0,
		const.groupJumpFreighter: 1000000.0,
		const.groupLogistics: 10000.0,
		const.groupMarauders: 50000.0,
		const.groupMiningBarge: 3750.0,
		const.groupSupercarrier: 1000000.0,
		const.groupRookieship: 2500.0,
		const.groupShuttle: 500.0,
		const.groupStealthBomber: 2500.0,
		const.groupTitan: 10000000.0,
		const.groupTransportShip: 20000.0,
		const.groupCargoContainer: 1000.0,
		const.groupMissionContainer: 1000.0,
		const.groupSecureCargoContainer: 1000.0,
		const.groupAuditLogSecureContainer: 1000.0,
		const.groupFreightContainer: 1000.0,
		const.groupStrategicCruiser: 5000.0,
		const.groupPrototypeExplorationShip: 500.0,
		}


	#-------------------------------------------------------------------------------------------------------------------
	# BulkData Table Definitions.
	# ver            - minimum machoNet version required to load this table with prime() method
	# del            - starting from this machoNet version the table no longer exists
	# cfg attrib     - name the table is accessed with in cfg.* (e.g. cfg.invtypes)
	# bulkdata name  - name of the bulkdata in the cache file if not same as cfg attrib, else None.
	# storage class  - container class for the table data. can be string to generate FilterRowset from named table.
	# row class      - the class used to wrap rows with when they are requested.
	# primary key    - primary key
	# bulkID         - bulkdata file ID
	#
	# this table is filtered for every instance to create a table dict containing only those entries relevant
	# to its protocol version.
	__tables__ = (

#		( cfg attrib                  , (ver, del, bulkdata name     , storage class       , row class         , primary key           bulkID)),
		("evegraphics"                , (  0,   0, "graphics"        , Recordset           , EveGraphics       , "graphicID"         , const.cacheResGraphics)),
		("icons"                      , (242,   0, None              , Recordset           , util.Row          , 'iconID'            , const.cacheResIcons)),
		("sounds"                     , (242,   0, None              , Recordset           , util.Row          , 'soundID'           , const.cacheResSounds)),

		("invcategories"              , (  0,   0, "categories"      , Recordset           , InvCategory       , "categoryID"        , const.cacheInvCategories)),
		("invgroups"                  , (  0,   0, "groups"          , Recordset           , InvGroup          , "groupID"           , const.cacheInvGroups)),
		("groupsByCategories"         , (  0,   0, None              , "invgroups"         , None              , "categoryID"        , None)),
		("invtypes"                   , (  0,   0, "types"           , Recordset           , InvType           , "typeID"            , const.cacheInvTypes)),
		("typesByGroups"              , (  0,   0, None              , "invtypes"          , None              , "groupID"           , None)),
		("typesByMarketGroups"        , (  0,   0, None              , "invtypes"          , None              , "marketGroupID"     , None)),
		("invmetagroups"              , (  0,   0, "metagroups"      , Recordset           , InvMetaGroup      , "metaGroupID"       , const.cacheInvMetaGroups)),
		("invmetatypes"               , (  0,   0, "metatypes"       , util.FilterRowset   , None              , "parentTypeID"      , const.cacheInvMetaTypes)),  # custom loader!
		("invmetatypesByTypeID"       , (  0,   0, None              , None                , None              , None                , None)),  # custom loader!
		("invbptypes"                 , (  0,   0, "bptypes"         , Recordset           , util.Row          , "blueprintTypeID"   , const.cacheInvBlueprintTypes)),
		("invreactiontypes"           , (  0,   0, "invtypereactions", util.FilterRowset   , None              , "reactionTypeID"    , const.cacheInvTypeReactions)),
		("invcontrabandTypesByFaction", (  0,   0, None              , dict                , None              , None                , None)),  # custom loader!
		("invcontrabandTypesByType"   , (  0,   0, None              , dict                , None              , None                , None)),  # custom loader!
		("shiptypes"                  , (  0,   0, None              , util.IndexRowset    , util.Row          , "shipTypeID"        , const.cacheShipTypes)),

		("dgmattribs"                 , (  0,   0, None              , ItemsRecordset      , DgmAttribute      , "attributeID"       , const.cacheDogmaAttributes)),
		("dgmeffects"                 , (  0,   0, None              , ItemsRecordset      , DgmEffect         , "effectID"          , const.cacheDogmaEffects)),
		("dgmtypeattribs"             , (  0,   0, None              , util.IndexedRowLists, util.Row          , ('typeID',)         , const.cacheDogmaTypeAttributes)),
		("dgmtypeeffects"             , (  0,   0, None              , util.IndexedRowLists, util.Row          , ('typeID',)         , const.cacheDogmaTypeEffects)),
		("dgmexpressions"             , (297,   0, None              , Recordset           , util.Row          , 'expressionID'      , const.cacheDogmaExpressions)),

		("eveunits"                   , (  0,   0, "units"           , Recordset           , util.Row          , "unitID"            , const.cacheDogmaUnits)),

		("ramaltypes"                 , (  0,   0, None              , Recordset           , util.Row          , "assemblyLineTypeID", const.cacheRamAssemblyLineTypes)),
		("ramactivities"              , (  0,   0, None              , Recordset           , RamActivity       , "activityID"        , const.cacheRamActivities)),
		("ramcompletedstatuses"       , (  0, 276, None              , Recordset           , RamCompletedStatus, "completedStatusID" , None)),
		("ramcompletedstatuses"       , (276,   0, None              , Recordset           , RamCompletedStatus, "completedStatus"   , const.cacheRamCompletedStatuses)),
		("ramaltypesdetailpercategory", (  0,   0, None              , util.FilterRowset   , RamDetail         , "assemblyLineTypeID", const.cacheRamAssemblyLineTypesCategory)),
		("ramaltypesdetailpergroup"   , (  0,   0, None              , util.FilterRowset   , RamDetail         , "assemblyLineTypeID", const.cacheRamAssemblyLineTypesGroup)),

		("billtypes"                  , (  0,   0, None              , Recordset           , Billtype          , 'billTypeID'        , const.cacheActBillTypes)),
		("certificates"               , (  0,   0, None              , Recordset           , Certificate       , "certificateID"     , const.cacheCertificates)),
		("certificaterelationships"   , (  0,   0, None              , Recordset           , util.Row          , "relationshipID"    , const.cacheCertificateRelationships)),

		("mapcelestialdescriptions"   , (  0, 276, None              , Recordset           , MapCelestialDescription, "celestialID"  , None)),
		("mapcelestialdescriptions"   , (276,   0, None              , Recordset           , MapCelestialDescription, "itemID"       , const.cacheMapCelestialDescriptions)),
		("locationwormholeclasses"    , (  0,   0, None              , Recordset           , util.Row          , "locationID"        , const.cacheMapLocationWormholeClasses)),
		("locationscenes"             , (242, 298, None              , Recordset           , util.Row          , 'locationID'        , const.cacheMapLocationScenes)),

		("schematics"                 , (242,   0, None              , Recordset           , Schematic         , 'schematicID'       , const.cachePlanetSchematics)),
		("schematicstypemap"          , (242,   0, None              , util.FilterRowset   , None              , 'schematicID'       , const.cachePlanetSchematicsTypeMap)),  # custom loader!
		("schematicsByType"           , (242,   0, None              , util.FilterRowset   , None              , 'typeID'            , const.cachePlanetSchematicsTypeMap)),  # custom loader!
		("schematicspinmap"           , (242,   0, None              , util.FilterRowset   , None              , 'schematicID'       , const.cachePlanetSchematicsPinMap)),  # custom loader!
		("schematicsByPin"            , (242,   0, None              , util.FilterRowset   , None              , 'pinTypeID'         , const.cachePlanetSchematicsPinMap)),  # custom loader!

		("ramtyperequirements"        , (242,   0, None              , dict                , None          , ('typeID', 'activityID'), const.cacheRamTypeRequirements)),
		("ramtypematerials"           , (242, 254, None              , dict                , None              , 'typeID'            , None)),
		("invtypematerials"           , (254,   0, None              , dict                , None              , 'typeID'            , const.cacheInvTypeMaterials)),

		("evelocations"               , (  0,   0, "locations"       , Recordset           , EveLocations      , "locationID"        , None)),  # custom loader!
		("factions"                   , (276,   0, None              , Recordset           , util.Row          , "factionID"         , const.cacheChrFactions)),
		("npccorporations"            , (276,   0, None              , Recordset           , util.Row          , "corporationID"     , const.cacheCrpNpcCorporations)),
		("eveowners"                  , (  0,   0, "owners"          , Recordset           , EveOwners         , "ownerID"           , const.cacheChrNpcCharacters)),  # custom loader!
		("corptickernames"            , (  0,   0, "tickernames"     , Recordset           , CrpTickerNames    , "corporationID"     , const.cacheCrpTickerNamesStatic)),

#		("planetattributes"           , (242,   0, None              , None                , None              , None)),  # N/A

		# FIXME for 276+

		# this seems to be gone.
		("ownericons"                 , (242, 276, None              , Recordset           , util.Row          , 'ownerID'           , None)),

		# this seems to be on-demand now, not in bulkdata.
		("allianceshortnames"         , (  0, 276, None              , Recordset           , AllShortNames     , "allianceID"        , None)),

		# location stuff.
		("regions"                    , (299,   0, None              , Recordset           , util.Row          , "regionID"          , const.cacheMapRegionsTable)),
		("constellations"             , (299,   0, None              , Recordset           , util.Row          , "constellationID"   , const.cacheMapConstellationsTable)),
		("solarsystems"               , (299,   0, None              , Recordset           , util.Row          , "solarSystemID"     , const.cacheMapSolarSystemsTable)),
		("stations"                   , (299,   0, None              , Recordset           , util.Row          , "stationID"         , const.cacheStaStationsStatic)),
		("evelocations"               , (  0,   0, "locations"       , Recordset           , EveLocations      , "locationID"        , None)),  # custom loader!
	)

	# Custom table loader methods follow

	@_memoize
	def eveowners(self):
		if self.protocol >= 276:
			bloodlinesToTypes = {
				const.bloodlineDeteis   : const.typeCharacterDeteis,
				const.bloodlineCivire   : const.typeCharacterCivire,
				const.bloodlineSebiestor: const.typeCharacterSebiestor,
				const.bloodlineBrutor   : const.typeCharacterBrutor,
				const.bloodlineAmarr    : const.typeCharacterAmarr,
				const.bloodlineNiKunni  : const.typeCharacterNiKunni,
				const.bloodlineGallente : const.typeCharacterGallente,
				const.bloodlineIntaki   : const.typeCharacterIntaki,
				const.bloodlineStatic   : const.typeCharacterStatic,
				const.bloodlineModifier : const.typeCharacterModifier,
				const.bloodlineAchura   : const.typeCharacterAchura,
				const.bloodlineJinMei   : const.typeCharacterJinMei,
				const.bloodlineKhanid   : const.typeCharacterKhanid,
				const.bloodlineVherokior: const.typeCharacterVherokior
			}

			if self.compatibility:
				rs = Recordset(EveOwners, 'ownerID', self)
				rs.header = ['ownerID', 'ownerName', 'typeID']
				d = rs.data
			else:
				rs = util.IndexRowset(['ownerID', 'ownerName', 'typeID'], None, key="ownerID", RowClass=EveOwners, cfgInstance=self)
				d = rs.items

			rd = blue.DBRowDescriptor((('ownerID', const.DBTYPE_I4), ('ownerName', const.DBTYPE_WSTR), ('typeID', const.DBTYPE_I2)))

			DBRow = blue.DBRow
			for row in self.factions:
				id_ = row.factionID
				d[id_] = DBRow(rd, [id_, row.factionName, const.typeFaction])

			for row in self.npccorporations:
				id_ = row.corporationID
				d[id_] = DBRow(rd, [id_, row.corporationName, const.typeCorporation])

			for row in self.cache.LoadBulk(const.cacheChrNpcCharacters):
				id_ = row.characterID
				d[id_] = DBRow(rd, [id_, row.characterName, bloodlinesToTypes[row.bloodlineID]])

			d[1] = DBRow(rd, [1, 'EVE System', 0])

		else:
			rs = self._loadbulkdata("owners", Recordset, EveOwners, "ownerID")
			self._loadbulkdata("config.StaticOwners", dest=rs)

		rs.lines = rs.items.values()
		return rs


	@_memoize
	def evelocations(self):
		if self.protocol >= 276:
			if self.compatibility:
				rs = Recordset(EveLocations, 'locationID', self)
				rs.header = ['locationID', 'locationName', 'x', 'y', 'z']
				d = rs.data
			else:
				rs = util.IndexRowset(['locationID', 'locationName', 'x', 'y', 'z'], None, key="locationID", RowClass=EveLocations, cfgInstance=self)
				d = rs.items

			rd = blue.DBRowDescriptor((('locationID', const.DBTYPE_I4), ('locationName', const.DBTYPE_WSTR), ('x', const.DBTYPE_R8), ('y', const.DBTYPE_R8), ('z', const.DBTYPE_R8)))
			DBRow = blue.DBRow

			for table, name in (
				(self.regions, "region"),
				(self.constellations, "constellation"),
				(self.solarsystems, "solarSystem"),
				(self.stations, "station"),
			):
				hdr = table.header
				id_ix = hdr.index(name + "ID")
				name_ix = hdr.index(name + "Name")
				for row in table.lines:
					id_ = row[id_ix]
					d[id_] = DBRow(rd, [id_, row[name_ix], row.x, row.y, -row.z])
		else:
			rs = self._loadbulkdata("locations", Recordset, EveLocations, "locationID")
			self._loadbulkdata("config.StaticLocations", dest=rs)

		rs.lines = rs.items.values()
		return rs


	#--

	def _invcontrabandtypes_load(self):
		byFaction = self.invcontrabandTypesByFaction = {}
		byType = self.invcontrabandFactionsByType = {}

		if self.protocol >= 276:
			obj = self.cache.LoadBulk(const.cacheInvContrabandTypes)
		else:
			obj = self.cache.LoadObject("config.InvContrabandTypes")

		for each in obj:
			typeID = each.typeID
			factionID = each.factionID

			if factionID not in byFaction:
				byFaction[factionID] = {}
			byFaction[factionID][typeID] = each
			if typeID not in byType:
				byType[typeID] = {}
			byType[typeID][factionID] = each

	@_memoize
	def invcontrabandTypesByFaction(self):
		self._invcontrabandtypes_load()
		return self.invcontrabandTypesByFaction

	@_memoize
	def invcontrabandTypesByType(self):
		self._invcontrabandtypes_load()
		return self.invcontrabandFactionsByType


	#--

	def _schematicstypemap_load(self):
		if self.protocol >= 276:
			obj = self.cache.LoadBulk(const.cachePlanetSchematicsTypeMap)
		else:
			obj = self.cache.LoadObject("config.BulkData.schematicstypemap")

		header = obj.header.Keys()
		self.schematicstypemap = util.FilterRowset(header, obj, "schematicID")
		self.schematicsByType = util.FilterRowset(header, obj, "typeID")

	@_memoize
	def schematicstypemap(self):
		self._schematicstypemap_load()
		return self.schematicstypemap

	@_memoize
	def schematicsByType(self):
		self._schematicstypemap_load()
		return self.schematicsByType

	#--

	def _schematicspinmap_load(self):
		if self.protocol >= 276:
			obj = self.cache.LoadBulk(const.cachePlanetSchematicsPinMap)
		else:
			obj = self.cache.LoadObject("config.BulkData.schematicspinmap")

		header = obj.header.Keys()
		self.schematicspinmap = util.FilterRowset(header, obj, "schematicID")
		self.schematicsByPin = util.FilterRowset(header, obj, "pinTypeID")

	@_memoize
	def schematicspinmap(self):
		self._schematicspinmap_load()
		return self.schematicspinmap

	@_memoize
	def schematicsByPin(self):
		self._schematicspinmap_load()
		return self.schematicsByPin

	#--

	def _invmetatypes_load(self):
		if self.protocol >= 276:
			obj = self.cache.LoadBulk(const.cacheInvMetaTypes)
		else:
			obj = self.cache.LoadObject("config.BulkData.invmetatypes")

		if type(obj) is tuple:
			# old style.
			self.invmetatypes = util.FilterRowset(obj[0], obj[1], "parentTypeID")
			self.invmetatypesByTypeID = util.FilterRowset(obj[0], obj[1], "typeID")
		else:
			header = obj.header.Keys()
			self.invmetatypes = util.FilterRowset(header, obj, "parentTypeID")
			self.invmetatypesByTypeID = util.FilterRowset(header, obj, "typeID")

	@_memoize
	def invmetatypes(self):
		self._invmetatypes_load()
		return self.invmetatypes

	@_memoize
	def invmetatypesByTypeID(self):
		self._invmetatypes_load()
		return self.invmetatypesByTypeID

	#--

	def __init__(self, cache, compatibility=False):
		self.cache = cache
		self.callback = None
		self.compatibility = compatibility
		protocol = self.protocol = self.cache.machoVersion

		# Figure out the set of tables managed by this instance.
		# Only tables that are available for this instance's particular
		# machoNet version will be in this set, and are the only tables loaded
		# when prime() is called.
		self._tables = dict(((k, v) for k, v in self.__tables__ if protocol >= v[0] and protocol < v[1] or 2147483647))
		self.tables = frozenset(( \
			attrName for attrName in dir(self.__class__) \
			if isinstance(getattr(self.__class__, attrName), _memoize) \
			and protocol >= self._tables[attrName][0] \
			and protocol < (self._tables[attrName][1] or 2147483647) \
		))
		self._attrCache = {}


	def release(self):
		# purge all loaded tables

		for tableName in self.tables:
			try:
				delattr(self, tableName)
			except AttributeError:
				pass

		self._attrCache = {}


	def _loadbulkdata(self, tableName=None, storageClass=None, rowClass=None, primaryKey=None, dest=None, bulkID=None):

		fullTableName = tableName if tableName.startswith("config.") else "config.BulkData."+tableName

		if dest:
			# This is hint data; just add it to the specified table (dest)
			# Assumes dest is an IndexRowset compatible object.


			if self.protocol >= 276:
				# Incarna 1.0.2 load method
				obj = self.cache.LoadBulk(bulkID)
			else:
				# legacy load method
				obj = self.cache.LoadObject(tableName)

			if not obj:
				raise RuntimeError("table '%s' (%d) not found in bulkdata" % (tableName, bulkID))

			rs = dest
			if type(obj) is not dbutil.CRowset:
				# pre-Tyrannis (protocol 235) this was a Rowset, not a CRowset.
				obj = obj.lines

			# add the lines
			rs.lines.extend(obj)

			# fix index
			ki = rs.key
			i = rs.items
			for line in obj:
				i[line[ki]] = line

			return rs

		if type(storageClass) is str:
			# create a FilterRowset from existing table named by storageClass.
			table = getattr(self, storageClass)
			if self.compatibility:
				rs = util.FilterRowset(table.header, table.data.values(), primaryKey)
			else:
				rs = table.GroupedBy(primaryKey)
			return rs

		if self.protocol >= 276:
			# Incarna 1.0.2 load method
			obj = self.cache.LoadBulk(bulkID)
		else:
			# legacy load method
			obj = self.cache.LoadObject(fullTableName)

		if issubclass(storageClass, Recordset):
			if self.compatibility:
				# use the Recordsets like EVE, for compatibility (don't ask).

				rs = storageClass(rowClass, primaryKey, self)
				data = rs.data

				if type(obj) is dbutil.CRowset:
					rs.header = obj.header.Keys()
					keycol = rs.header.index(primaryKey)
					for i in obj:
						a = list(i)
						data[a[keycol]] = a
				else:
					rs.header = obj[0]
					keycol = rs.header.index(primaryKey)
					for i in obj[1]:
						data[i[keycol]] = i
			else:
				# Custom loading; uses IndexRowset for the data instead of Recordset.
				# Faster, and IndexRowsets have more functionality.
				if type(obj) is dbutil.CRowset:
					rs = util.IndexRowset(obj.header.Keys(), obj, key=primaryKey, RowClass=rowClass, cfgInstance=self)
				else:
					rs = util.IndexRowset(obj[0], obj[1], key=primaryKey, RowClass=rowClass, cfgInstance=self)

		elif issubclass(storageClass, util.FilterRowset):
			rs = storageClass(obj.header.Keys(), obj, primaryKey)

		elif issubclass(storageClass, util.IndexedRowLists):
			rs = storageClass(obj, keys=primaryKey)

		elif issubclass(storageClass, util.IndexRowset):
			if type(obj) is tuple:
				# old style.
				rs = storageClass(obj[0], obj[1], "shipTypeID")
			else:
				rs = storageClass(obj.header.Keys(), obj, "shipTypeID")

		elif issubclass(storageClass, dict):
			rs = {}
			if type(primaryKey) is tuple:
				getkey = lambda row: tuple(map(row.__getitem__, primaryKey))
			else:
				getkey = lambda row: getattr(row, primaryKey)

			for row in obj:
				key = getkey(row)
				li = rs.get(key, False)
				if li:
					li.append(row)
				else:
					rs[key] = [row]

		else:
			raise RuntimeError("Invalid storageClass: %s" % storageClass)

		return rs


	def prime(self, tables=None, callback=None, debug=False):
		"""Loads the tables named in the tables sequence. If no tables are
specified, it will load all supported ones. A callback function can be provided
which will be called as func(current, total, tableName).

		This method should be used in the following situations:
		- The ConfigMgr instance is going to be used in a multi-threaded app.
		- The Application wants to load all data at once instead of on access.
		"""

		if debug:
			self._debug = True
			start = time.clock()
			print >>sys.stderr, "LOADING STATIC DATABASE"
			print >>sys.stderr, "  machoCachePath:", self.cache.machocachepath
			print >>sys.stderr, "  machoVersion:", self.cache.machoVersion

		try:
			if tables is None:
				# preload everything.
				tables = self.tables
			else:
				# preload specified only.
				tables = frozenset(tables)
				invalid = tables - self.tables
				if invalid:
					raise ValueError("Unknown table(s): %s" % ", ".join(invalid))

			current = 0
			total = len(tables)
		
			for tableName in tables:

				if callback:
					callback(current, total, tableName)
					current += 1

				if debug:
					print >>sys.stderr, "  priming:", tableName
				# now simply trigger the property's getters
				getattr(self, tableName)

		finally:
			if debug:
				self._debug = False

		if debug:
			t = time.clock() - start
			print >>sys.stderr, "Priming took %ss (of which %ss decoding)" % (t, self.cache._time_load)


	def GetTypeVolume(self, typeID, singleton=1, qty=1):
		"""Returns total volume of qty units of typeID. 
		Uses packaged volume if singleton is non-zero.
		"""
		if typeID == const.typePlasticWrap:
			raise RuntimeError("GetTypeVolume: cannot determine volume of plastic from type alone")

		rec = cfg.invtypes.Get(typeID)
		if rec.Group().categoryID == const.categoryShip and not singleton and rec.groupID in self.__containerVolumes__ and typeID != const.typeBHMegaCargoShip:
			volume = self.__containerVolumes__[rec.groupID]
		else:
			volume = rec.volume

		if volume != -1:
			return volume * qty

		return volume


	def GetTypeAttrDict(self, typeID):
		"""Returns (cached) dictionary of attributes for specified type."""
		attr = self._attrCache.get(typeID, None)
		if attr is None:
			self._attrCache[typeID] = attr = {}
			for row in self.dgmtypeattribs[typeID]:
				attr[row.attributeID] = row.value
		return attr


	def GetRequiredSkills(self, typeID):
		"""Returns list of (requiredSkillTypeID, requiredLevel) tuples."""
		attr = self.GetTypeAttrDict(typeID)
		reqs = []
		for i in xrange(1, 7):
			skillID = attr.get(getattr(const, "attributeRequiredSkill%s" % i), False)
			if skillID:
				lvl = attr.get(getattr(const, "attributeRequiredSkill%sLevel" % i), None)
				if lvl is not None:
					reqs.append((skillID, lvl))
		return reqs


	def GetTypeAttribute(self, typeID, attributeID, defaultValue=None):
		"""Return specified dogma attribute for given type, or custom default value."""
		attr = self.GetTypeAttrDict(typeID)
		return attr.get(attributeID, defaultValue)


	def GetTypeAttribute2(self, typeID, attributeID):
		"""Return specified dogma attribute for given type, or default attribute value."""
		attr = self.GetTypeAttrDict(typeID)
		value = attr.get(attributeID, None)
		if value is None:
			return self.dgmattribs.Get(attributeID).defaultValue
		return value


	def GetLocationWormholeClass(self, solarSystemID, constellationID, regionID):
		rec = self.locationwormholeclasses.Get(solarSystemID, None) \
		or self.locationwormholeclasses.Get(constellationID, None) \
		or self.locationwormholeclasses.Get(regionID, None)
		if rec:
			return rec.wormholeClassID
		return 0

