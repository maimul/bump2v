import argparse
from datetime import datetime, timezone
import glob
import io
import itertools
import logging
import os
import re
import sys
import tomllib
import warnings
from configparser import (
    ConfigParser,
    RawConfigParser,
    NoOptionError,
)

from . import __version__, __title__
from .version_part import (
    VersionConfig,
    NumericVersionPartConfiguration,
    ConfiguredVersionPartConfiguration,
)
from .exceptions import (
    IncompleteVersionRepresentationException,
    MissingValueForSerializationException,
    VersionNotFoundException,
    WorkingDirectoryIsDirtyException,
)

from .utils import (
    ConfiguredFile,
    DiscardDefaultIfSpecifiedAppendAction,
    FileChange,
    keyvaluestring,
    prefixed_environ,
    read_text_raw,
    write_all,
)
from .vcs import Git, Mercurial


DESCRIPTION = "{}: v{} (using Python v{})".format(
    __title__,
    __version__,
    sys.version.split("\n")[0].split(" ")[0]
)
VCS = [Git, Mercurial]

RE_DETECT_SECTION_TYPE = re.compile(
    r"^bumpversion:"
    r"((?P<file>file|glob)(\s*\(\s*(?P<file_suffix>[^\):]+)\)?)?|(?P<part>part)):"
    r"(?P<value>.+)",
)

logger_list = logging.getLogger("bumpversion.list")
logger = logging.getLogger(__name__)
time_context = {"now": datetime.now(), "utcnow": datetime.now(timezone.utc).replace(tzinfo=None)}
special_char_context = {c: c for c in ("#", ";")}


OPTIONAL_ARGUMENTS_THAT_TAKE_VALUES = [
    "--config-file",
    "--current-version",
    "--message",
    "--new-version",
    "--parse",
    "--serialize",
    "--search",
    "--replace",
    "--tag-name",
    "--tag-message",
    "-m",
]


def _handle_tag_only(known_args):
    """Tag the current HEAD with the current_version from config, without bumping."""
    explicit_config = getattr(known_args, "config_file", None)
    config_file = _determine_config_file(explicit_config)
    config, config_file_exists, _, _, _ = _load_configuration(config_file, explicit_config, {})

    if not config_file_exists:
        logger.error("No config file found — cannot determine current version for tagging")
        sys.exit(1)

    cfg = dict(config.items("bumpversion"))
    current_version = cfg.get("current_version")
    if not current_version:
        logger.error("No current_version set in config — cannot create tag")
        sys.exit(1)

    sign_tags = cfg.get("sign_tags", False)
    if isinstance(sign_tags, str):
        sign_tags = sign_tags.lower() in ("true", "1", "yes")

    tag_name_tmpl = cfg.get("tag_name", "v{new_version}")
    tag_message_tmpl = cfg.get("tag_message", "Bump version: {current_version} → {new_version}")

    ctx = {"new_version": current_version, "current_version": current_version}
    ctx.update(time_context)
    ctx.update(prefixed_environ())
    ctx.update(special_char_context)

    tag_name = tag_name_tmpl.format(**ctx)
    tag_message = tag_message_tmpl.format(**ctx)

    for vcs_cls in VCS:
        if vcs_cls.is_usable():
            vcs_cls.tag(sign_tags, tag_name, tag_message)
            logger.info("Tagged HEAD as '%s'", tag_name)
            print("Tagged HEAD as '{}'".format(tag_name))
            return

    logger.error("No usable VCS found for tagging")
    sys.exit(1)


class Settings:
    """The parsed arguments, the config and the current version. Built by load_settings()."""

    def __init__(self, **fields):
        self.__dict__.update(fields)


class Plan(Settings):
    """Everything a bump will do, worked out before anything is written.

    Built by compute_plan(), carried out by apply_plan().
    """

    def vcs_context(self):
        return _vcs_context(self.args, self.current_version, self.new_version)

    def commit_message(self):
        return self.args.message.format(**self.vcs_context())

    def tag_name(self):
        return self.args.tag_name.format(**self.vcs_context())


def main(original_args=None):
    args, known_args, root_parser, positionals = _parse_arguments_phase_1(original_args)
    _setup_logging(known_args.list, known_args.verbose)

    # #256: --tag-only creates a tag on HEAD without bumping
    if known_args.tag_only:
        _handle_tag_only(known_args)
        return

    plan = _compute_plan(args, known_args, root_parser, positionals)
    apply_plan(plan)


def compute_plan(original_args=None):
    """Parse the arguments and config and work out the bump, without writing anything."""
    args, known_args, root_parser, positionals = _parse_arguments_phase_1(original_args)
    _setup_logging(known_args.list, known_args.verbose)
    return _compute_plan(args, known_args, root_parser, positionals)


def load_settings(original_args=None):
    """Parse the arguments and config without computing a new version (no part needed)."""
    args, known_args, root_parser, positionals = _parse_arguments_phase_1(original_args)
    _setup_logging(known_args.list, known_args.verbose)
    return _load_settings(args, known_args, root_parser, positionals)


def _load_settings(args, known_args, root_parser, positionals):
    vcs_info = _determine_vcs_usability()
    defaults = _determine_current_version(vcs_info)
    explicit_config = None
    if hasattr(known_args, "config_file"):
        explicit_config = known_args.config_file
    config_file = _determine_config_file(explicit_config)
    config, config_file_exists, config_newlines, part_configs, files = _load_configuration(
        config_file, explicit_config, defaults,
    )
    known_args, parser2, remaining_argv = _parse_arguments_phase_2(
        args, known_args, defaults, root_parser
    )
    version_config = _setup_versionconfig(known_args, part_configs)
    current_version = version_config.parse(known_args.current_version)
    return Settings(
        args=args,
        known_args=known_args,
        positionals=positionals,
        vcs_info=vcs_info,
        defaults=defaults,
        config_file=config_file,
        config=config,
        config_file_exists=config_file_exists,
        config_newlines=config_newlines,
        part_configs=part_configs,
        files=files,
        parser2=parser2,
        remaining_argv=remaining_argv,
        version_config=version_config,
        current_version=current_version,
    )


def _compute_plan(args, known_args, root_parser, positionals):
    s = _load_settings(args, known_args, root_parser, positionals)
    known_args, defaults, version_config = s.known_args, s.defaults, s.version_config
    current_version, files, config = s.current_version, s.files, s.config
    config_file, config_file_exists, config_newlines = (
        s.config_file, s.config_file_exists, s.config_newlines,
    )
    context = dict(
        itertools.chain(
            time_context.items(),
            prefixed_environ().items(),
            s.vcs_info.items(),
            special_char_context.items(),
        )
    )

    new_version = _assemble_new_version(
        context, current_version, defaults, known_args.current_version, positionals, version_config
    )
    args, file_names = _parse_arguments_phase_3(s.remaining_argv, positionals, defaults, s.parser2)
    new_version = _parse_new_version(args, new_version, version_config)

    if args.no_configured_files:
        files = []

    vcs = _determine_vcs_dirty(VCS, defaults, extra_files=getattr(args, "extra_files", None))
    files.extend(
        ConfiguredFile(file_name, version_config)
        for file_name
        in (file_names or positionals[1:])
    )
    _check_files_contain_version(files, current_version, context, getattr(args, "ignore_missing_version", False))
    changes = _compute_changes(files, current_version, new_version, context)
    config_text, config_change = _compute_config_update(
        config, config_file, config_newlines, config_file_exists, args.new_version,
    )
    if config_change and config_file.endswith(".toml"):
        # pyproject.toml is often both the config and a bumped file: apply both
        # edits to one text instead of letting the second write undo the first.
        for change in changes:
            if os.path.normpath(change.path) == os.path.normpath(config_file):
                change.after = _toml_set_current_version(change.after, args.new_version, config_file)
                config_change = None

    return Plan(
        changes=changes,
        config_text=config_text,
        config_change=config_change,
        args=args,
        defaults=defaults,
        config=config,
        config_file=config_file,
        config_file_exists=config_file_exists,
        config_newlines=config_newlines,
        files=files,
        version_config=version_config,
        current_version=current_version,
        new_version=new_version,
        context=context,
        vcs=vcs,
    )


def apply_plan(plan):
    """Write the files and the config, then commit and tag. Honours --dry-run."""
    args = plan.args
    for change in plan.changes:
        change.log(args.dry_run)
    _log_list(plan.config, args.new_version)

    write_to_config_file = (not args.dry_run) and plan.config_file_exists
    logger.info(
        "%s to config file %s:",
        "Would write" if not write_to_config_file else "Writing",
        plan.config_file,
    )
    logger.info(plan.config_text)

    # Every file is computed already; write them together so a failure part-way
    # through puts back what was written instead of leaving a half-bumped tree.
    if not args.dry_run:
        write_all(plan.changes + ([plan.config_change] if plan.config_change else []))

    if plan.vcs:
        context = _commit_to_vcs(plan.files, plan.context, plan.config_file,
                                 plan.config_file_exists, plan.vcs, args,
                                 plan.current_version, plan.new_version)
        _tag_in_vcs(plan.vcs, context, args)


def split_args_in_optional_and_positional(args):
    positions = []
    for i, arg in enumerate(args):

        previous = None

        if i > 0:
            previous = args[i - 1]

        if (not arg.startswith("-")) and (
            previous not in OPTIONAL_ARGUMENTS_THAT_TAKE_VALUES
        ):
            positions.append(i)

    positionals = [arg for i, arg in enumerate(args) if i in positions]
    args = [arg for i, arg in enumerate(args) if i not in positions]

    return (positionals, args)


def _parse_arguments_phase_1(original_args):
    positionals, args = split_args_in_optional_and_positional(
        sys.argv[1:] if original_args is None else original_args
    )
    if len(positionals[1:]) > 2:
        warnings.warn(
            "Giving multiple files on the command line will be deprecated, "
            "please use [bumpversion:file:...] in a config file.",
            PendingDeprecationWarning,
        )
    root_parser = argparse.ArgumentParser(add_help=False)
    root_parser.add_argument(
        "--config-file",
        metavar="FILE",
        default=argparse.SUPPRESS,
        required=False,
        help="Config file to read most of the variables from (default: .bumpversion.cfg)",
    )
    root_parser.add_argument(
        "--verbose",
        action="count",
        default=0,
        help="Print verbose logging to stderr",
        required=False,
    )
    root_parser.add_argument(
        "--list",
        action="store_true",
        default=False,
        help="List machine readable information",
        required=False,
    )
    root_parser.add_argument(
        "--allow-dirty",
        action="store_true",
        default=False,
        help="Don't abort if working directory is dirty",
        required=False,
    )
    root_parser.add_argument(
        "--tag-only",
        action="store_true",
        default=False,
        dest="tag_only",
        help="Create a tag for the current version on HEAD without bumping or committing",
        required=False,
    )
    known_args, _ = root_parser.parse_known_args(args)
    return args, known_args, root_parser, positionals


def _setup_logging(show_list, verbose):
    logformatter = logging.Formatter("%(message)s")
    if not logger.handlers:
        ch1 = logging.StreamHandler(sys.stderr)
        ch1.setFormatter(logformatter)
        logger.addHandler(ch1)
    if not logger_list.handlers:
        ch2 = logging.StreamHandler(sys.stdout)
        ch2.setFormatter(logformatter)
        logger_list.addHandler(ch2)
    if show_list:
        logger_list.setLevel(logging.DEBUG)
    try:
        log_level = [logging.WARNING, logging.INFO, logging.DEBUG][verbose]
    except IndexError:
        log_level = logging.DEBUG
    root_logger = logging.getLogger('')
    root_logger.setLevel(log_level)
    logger.debug("Starting %s", DESCRIPTION)


def _determine_vcs_usability():
    vcs_info = {}
    for vcs in VCS:
        if vcs.is_usable():
            vcs_info.update(vcs.latest_tag_info())
    return vcs_info


def _determine_current_version(vcs_info):
    defaults = {}
    if "current_version" in vcs_info:
        defaults["current_version"] = vcs_info["current_version"]
    return defaults


TOML_TABLE = ("tool", "bumpversion")


def _toml_table(path):
    """The [tool.bumpversion] table of a TOML file, or None if it has none."""
    with open(path, "rb") as f:
        data = tomllib.load(f)
    return data.get(TOML_TABLE[0], {}).get(TOML_TABLE[1])


def _determine_config_file(explicit_config):
    """Where the config lives. First found wins: --config-file, $BUMP2V_CONFIG,
    .bumpversion.cfg, .bumpversion.toml, pyproject.toml with [tool.bumpversion],
    setup.cfg."""
    if explicit_config:
        return explicit_config
    if os.environ.get("BUMP2V_CONFIG"):
        return os.environ["BUMP2V_CONFIG"]
    for candidate in (".bumpversion.cfg", ".bumpversion.toml"):
        if os.path.exists(candidate):
            return candidate
    if os.path.exists("pyproject.toml"):
        try:
            if _toml_table("pyproject.toml") is not None:
                return "pyproject.toml"
        except tomllib.TOMLDecodeError:
            pass
    if os.path.exists("setup.cfg"):
        return "setup.cfg"
    return ".bumpversion.cfg"


# [tool.bumpversion] options bump2v understands; anything else is reported and ignored.
_TOML_FILE_KEYS = {"search", "replace", "parse", "serialize", "ignore_missing_version", "replace_all"}
_TOML_PART_KEYS = {"values", "optional_value", "first_value"}


def _toml_value(value):
    if isinstance(value, bool):
        return "True" if value else "False"
    if isinstance(value, list):
        return "\n".join(str(v) for v in value)
    return str(value)


def _fill_config_from_toml(config_file, config):
    """Fill `config` from the [tool.bumpversion] table (bump-my-version's format), so
    the rest of the loader sees the same sections an INI file would give it."""
    table = _toml_table(config_file)
    if table is None:
        raise ValueError("{} has no [tool.bumpversion] table".format(config_file))

    for key, value in table.items():
        if key in ("files", "parts"):
            continue
        if isinstance(value, dict) or (isinstance(value, list) and key != "serialize"):
            logger.warning("Ignoring unsupported option %s in %s", key, config_file)
            continue
        config.set("bumpversion", key, _toml_value(value))

    seen = {}
    for entry in table.get("files", []):
        kind = "glob" if "glob" in entry else "file"
        target = entry.get("glob") or entry.get("filename")
        if not target:
            logger.warning("Ignoring a [[tool.bumpversion.files]] entry without filename or glob")
            continue
        # The same file can appear twice with different searches; INI section
        # names must be unique, and bumpversion:file(N):path is the INI way.
        seen[target] = seen.get(target, 0) + 1
        suffix = "({})".format(seen[target]) if seen[target] > 1 else ""
        section = "bumpversion:{}{}:{}".format(kind, suffix, target)
        config.add_section(section)
        for key, value in entry.items():
            if key in ("filename", "glob"):
                continue
            if key not in _TOML_FILE_KEYS:
                logger.warning("Ignoring unsupported option %s for %s", key, target)
                continue
            config.set(section, key, _toml_value(value))

    for name, part in table.get("parts", {}).items():
        section = "bumpversion:part:{}".format(name)
        config.add_section(section)
        for key, value in part.items():
            if key not in _TOML_PART_KEYS:
                logger.warning("Ignoring unsupported option %s for part %s", key, name)
                continue
            config.set(section, key, _toml_value(value))


_TOML_HEADER = re.compile(r"^\s*\[\[?\s*([^\]]+?)\s*\]\]?\s*(#.*)?$")
_TOML_CURRENT_VERSION = re.compile(r"""^(\s*current_version\s*=\s*)(["'])(.*?)\2""")


def _toml_set_current_version(text, new_version, path):
    """Set current_version under [tool.bumpversion], changing only that line."""
    lines = text.splitlines(keepends=True)
    table = None
    for i, line in enumerate(lines):
        header = _TOML_HEADER.match(line.rstrip("\r\n"))
        if header:
            table = header.group(1).replace(" ", "")
            continue
        if table == ".".join(TOML_TABLE):
            match = _TOML_CURRENT_VERSION.match(line)
            if match:
                quote = match.group(2)
                lines[i] = match.group(1) + quote + new_version + quote + line[match.end():]
                return "".join(lines)
    raise ValueError(
        'Could not find current_version = "..." under [tool.bumpversion] in {}'.format(path)
    )


def _to_bool(value, option, section):
    try:
        return RawConfigParser.BOOLEAN_STATES[value.strip().lower()]
    except KeyError:
        raise ValueError(
            "{} = {!r} in [{}] is not a boolean (use True or False)".format(option, value, section)
        )


def _load_configuration(config_file, explicit_config, defaults):
    if os.path.basename(config_file) == "setup.cfg":
        config = ConfigParser("")
    else:
        config = RawConfigParser("")
    config.optionxform = lambda option: option
    config.add_section("bumpversion")
    config_file_exists = os.path.exists(config_file)

    if not config_file_exists:
        message = "Could not read config file at {}".format(config_file)
        if explicit_config:
            raise argparse.ArgumentTypeError(message)
        logger.info(message)
        return config, config_file_exists, None, {}, []

    logger.info("Reading config file %s:", config_file)

    with open(config_file, "rt", encoding="utf-8-sig") as config_fp:
        config_content = config_fp.read()
        config_newlines = config_fp.newlines

    logger.info(config_content)
    if config_file.endswith(".toml"):
        _fill_config_from_toml(config_file, config)
    else:
        config.read_string(config_content)
    log_config = io.StringIO()
    config.write(log_config)

    if config.has_option("bumpversion", "files"):
        warnings.warn(
            "'files =' configuration will be deprecated, please use [bumpversion:file:...]",
            PendingDeprecationWarning,
        )

    defaults.update(dict(config.items("bumpversion")))

    for listvaluename in ("serialize",):
        try:
            value = config.get("bumpversion", listvaluename)
            defaults[listvaluename] = list(
                filter(None, (x.strip() for x in value.splitlines()))
            )
        except NoOptionError:
            pass

    for boolvaluename in ("commit", "tag", "dry_run", "sign_tags", "ignore_missing_version",
                          "replace_all", "push", "allow_dirty"):
        try:
            defaults[boolvaluename] = config.getboolean(
                "bumpversion", boolvaluename
            )
        except NoOptionError:
            pass

    # extra_files in config is a whitespace-separated list
    if "extra_files" in defaults and isinstance(defaults["extra_files"], str):
        defaults["extra_files"] = defaults["extra_files"].split()

    part_configs = {}
    files = []

    for section_name in config.sections():
        section_type_match = RE_DETECT_SECTION_TYPE.match(section_name)

        if not section_type_match:
            continue

        section_type = section_type_match.groupdict()
        section_value = section_type.get("value")
        section_config = dict(config.items(section_name))

        if section_type.get("part"):
            ThisVersionPartConfiguration = NumericVersionPartConfiguration

            if "values" in section_config:
                section_config["values"] = list(
                    filter(
                        None,
                        (x.strip() for x in section_config["values"].splitlines()),
                    )
                )
                ThisVersionPartConfiguration = ConfiguredVersionPartConfiguration

            part_configs[section_value] = ThisVersionPartConfiguration(
                **section_config
            )
        elif section_type.get("file"):
            filename = section_value

            if "serialize" in section_config:
                section_config["serialize"] = list(
                    filter(
                        None,
                        (
                            x.strip().replace("\\n", "\n")
                            for x in section_config["serialize"].splitlines()
                        ),
                    )
                )

            section_config["part_configs"] = part_configs

            if "parse" not in section_config:
                section_config["parse"] = defaults.get(
                    "parse", r"(?P<major>\d+)\.(?P<minor>\d+)\.(?P<patch>\d+)"
                )

            if "serialize" not in section_config:
                section_config["serialize"] = defaults.get(
                    "serialize", ["{major}.{minor}.{patch}"]
                )

            if "search" not in section_config:
                section_config["search"] = defaults.get(
                    "search", "{current_version}"
                )

            if "replace" not in section_config:
                section_config["replace"] = defaults.get("replace", "{new_version}")

            replace_all = section_config.pop("replace_all", defaults.get("replace_all", True))
            if isinstance(replace_all, str):
                replace_all = _to_bool(replace_all, "replace_all", section_name)

            version_config = VersionConfig(**section_config)
            if section_type.get("file") == "glob":
                for filename_glob in glob.glob(filename, recursive=True):
                    files.append(ConfiguredFile(filename_glob, version_config, replace_all))
            else:
                files.append(ConfiguredFile(filename, version_config, replace_all))
    return config, config_file_exists, config_newlines, part_configs, files


def _parse_arguments_phase_2(args, known_args, defaults, root_parser):
    parser2 = argparse.ArgumentParser(
        prog="bumpversion", add_help=False, parents=[root_parser]
    )
    parser2.set_defaults(**defaults)
    parser2.add_argument(
        "--current-version",
        metavar="VERSION",
        help="Version that needs to be updated",
        required=False,
    )
    parser2.add_argument(
        "--parse",
        metavar="REGEX",
        help="Regex parsing the version string",
        default=defaults.get(
            "parse", r"(?P<major>\d+)\.(?P<minor>\d+)\.(?P<patch>\d+)"
        ),
    )
    parser2.add_argument(
        "--serialize",
        metavar="FORMAT",
        action=DiscardDefaultIfSpecifiedAppendAction,
        help="How to format what is parsed back to a version",
        default=defaults.get("serialize", ["{major}.{minor}.{patch}"]),
    )
    parser2.add_argument(
        "--search",
        metavar="SEARCH",
        help="Template for complete string to search",
        default=defaults.get("search", "{current_version}"),
    )
    parser2.add_argument(
        "--replace",
        metavar="REPLACE",
        help="Template for complete string to replace",
        default=defaults.get("replace", "{new_version}"),
    )
    known_args, remaining_argv = parser2.parse_known_args(args)

    defaults.update(vars(known_args))

    assert isinstance(known_args.serialize, list), "Argument `serialize` must be a list"

    return known_args, parser2, remaining_argv


def _setup_versionconfig(known_args, part_configs):
    try:
        version_config = VersionConfig(
            parse=known_args.parse,
            serialize=known_args.serialize,
            search=known_args.search,
            replace=known_args.replace,
            part_configs=part_configs,
        )
    except re.error:
        sys.exit(1)
    return version_config


def _assemble_new_version(
    context, current_version, defaults, arg_current_version, positionals, version_config
):
    new_version = None
    if "new_version" not in defaults and arg_current_version:
        try:
            if current_version and positionals:
                logger.info("Attempting to increment part '%s'", positionals[0])
                new_version = current_version.bump(positionals[0], version_config.order())
                logger.info("Values are now: %s", keyvaluestring(new_version._values))
                defaults["new_version"] = version_config.serialize(new_version, context)
        except MissingValueForSerializationException as e:
            logger.info("Opportunistic finding of new_version failed: %s", e.message)
        except IncompleteVersionRepresentationException as e:
            logger.info("Opportunistic finding of new_version failed: %s", e.message)
        except KeyError as e:
            logger.info("Opportunistic finding of new_version failed")
    return new_version


def _parse_arguments_phase_3(remaining_argv, positionals, defaults, parser2):
    parser3 = argparse.ArgumentParser(
        prog="bumpversion",
        description=DESCRIPTION,
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        conflict_handler="resolve",
        parents=[parser2],
    )
    parser3.set_defaults(**defaults)
    parser3.add_argument(
        "--current-version",
        metavar="VERSION",
        help="Version that needs to be updated",
        required="current_version" not in defaults,
    )
    parser3.add_argument(
        "--no-configured-files",
        action="store_true",
        default=False,
        dest="no_configured_files",
        help="Only replace the version in files specified on the command line, ignoring the files from the configuration file.",
    )
    parser3.add_argument(
        "--dry-run",
        "-n",
        action="store_true",
        default=False,
        help="Don't write any files, just pretend.",
    )
    parser3.add_argument(
        "--new-version",
        metavar="VERSION",
        help="New version that should be in the files",
        required="new_version" not in defaults,
    )
    commitgroup = parser3.add_mutually_exclusive_group()
    commitgroup.add_argument(
        "--commit",
        action="store_true",
        dest="commit",
        help="Commit to version control",
        default=defaults.get("commit", False),
    )
    commitgroup.add_argument(
        "--no-commit",
        action="store_false",
        dest="commit",
        help="Do not commit to version control",
        default=argparse.SUPPRESS,
    )
    taggroup = parser3.add_mutually_exclusive_group()
    taggroup.add_argument(
        "--tag",
        action="store_true",
        dest="tag",
        default=defaults.get("tag", False),
        help="Create a tag in version control",
    )
    taggroup.add_argument(
        "--no-tag",
        action="store_false",
        dest="tag",
        help="Do not create a tag in version control",
        default=argparse.SUPPRESS,
    )
    signtagsgroup = parser3.add_mutually_exclusive_group()
    signtagsgroup.add_argument(
        "--sign-tags",
        action="store_true",
        dest="sign_tags",
        help="Sign tags if created",
        default=defaults.get("sign_tags", False),
    )
    signtagsgroup.add_argument(
        "--no-sign-tags",
        action="store_false",
        dest="sign_tags",
        help="Do not sign tags if created",
        default=argparse.SUPPRESS,
    )
    parser3.add_argument(
        "--tag-name",
        metavar="TAG_NAME",
        help="Tag name (only works with --tag)",
        default=defaults.get("tag_name", "v{new_version}"),
    )
    parser3.add_argument(
        "--tag-message",
        metavar="TAG_MESSAGE",
        dest="tag_message",
        help="Tag message",
        default=defaults.get(
            "tag_message", "Bump version: {current_version} → {new_version}"
        ),
    )
    parser3.add_argument(
        "--message",
        "-m",
        metavar="COMMIT_MSG",
        help="Commit message",
        default=defaults.get(
            "message", "Bump version: {current_version} → {new_version}"
        ),
    )
    parser3.add_argument(
        "--commit-args",
        metavar="COMMIT_ARGS",
        help="Extra arguments to commit command",
        default=defaults.get("commit_args", ""),
    )
    parser3.add_argument(
        "--ignore-missing-version",
        action="store_true",
        default=defaults.get("ignore_missing_version", False),
        dest="ignore_missing_version",
        help="Ignore files where the version string is not found instead of raising an error",
    )
    parser3.add_argument(
        "--extra-files",
        metavar="FILE",
        nargs="*",
        default=defaults.get("extra_files", []),
        dest="extra_files",
        help="Extra files to stage and include in the version bump commit even if not modified by bumpversion",
    )
    file_names = []
    if "files" in defaults:
        assert defaults["files"] is not None
        file_names = defaults["files"].split(" ")
    parser3.add_argument("part", help="Part of the version to be bumped.")
    parser3.add_argument(
        "files", metavar="file", nargs="*", help="Files to change", default=file_names
    )
    args = parser3.parse_args(remaining_argv + positionals)

    if args.dry_run:
        logger.info("Dry run active, won't touch any files.")

    return args, file_names


def _parse_new_version(args, new_version, vc):
    if args.new_version:
        new_version = vc.parse(args.new_version)
    logger.info("New version will be '%s'", args.new_version)
    return new_version


def _determine_vcs_dirty(possible_vcses, defaults, extra_files=None):
    for vcs in possible_vcses:
        if not vcs.is_usable():
            continue

        try:
            vcs.assert_nondirty(allowed_paths=extra_files)
        except WorkingDirectoryIsDirtyException as e:
            if not defaults["allow_dirty"]:
                logger.warning(
                    "%s\n\nUse --allow-dirty to override this if you know what you're doing.",
                    e.message,
                )
                raise

        return vcs

    return None


def _check_files_contain_version(files, current_version, context, ignore_missing=False):
    logger.info(
        "Asserting files %s contain the version string...",
        ", ".join([str(f) for f in files]),
    )
    for f in files:
        try:
            f.should_contain_version(current_version, context)
        except VersionNotFoundException:
            if ignore_missing:
                logger.warning(
                    "Version string not found in '%s' — skipping (--ignore-missing-version)", f.path
                )
            else:
                raise


def _log_list(config, new_version):
    config.set("bumpversion", "new_version", new_version)
    for key, value in config.items("bumpversion"):
        logger_list.info("%s=%s", key, value)
    config.remove_option("bumpversion", "new_version")


def _compute_changes(files, current_version, new_version, context):
    """One FileChange per file. A file listed more than once (different searches)
    gets its edits applied one after another to the same text."""
    changes = {}
    for f in files:
        key = os.path.normpath(f.path)
        previous = changes.get(key)
        change = f.compute_replacement(current_version, new_version, context, previous)
        if previous is None:
            changes[key] = change
        else:
            previous.after = change.after
            previous.matches += change.matches
    return list(changes.values())


def _compute_config_update(config, config_file, config_newlines, config_file_exists,
                           new_version):
    """The config file's text with current_version set to new_version.

    Returns (text, FileChange or None). `config` itself is left unchanged. The
    file is written with one newline style: its own, or \\n if it mixed them.
    """
    if config_file.endswith(".toml") and config_file_exists:
        before, had_bom = read_text_raw(config_file)
        after = _toml_set_current_version(before, new_version, config_file)
        return after, FileChange(config_file, before, after, had_bom)

    had_option = config.has_option("bumpversion", "current_version")
    previous = config.get("bumpversion", "current_version", raw=True) if had_option else None
    config.set("bumpversion", "current_version", new_version)
    buffer = io.StringIO()
    config.write(buffer)
    if had_option:
        config.set("bumpversion", "current_version", previous)
    else:
        config.remove_option("bumpversion", "current_version")

    text = buffer.getvalue().strip() + "\n"
    if not config_file_exists:
        return text, None

    newline = config_newlines if isinstance(config_newlines, str) else "\n"
    before, had_bom = read_text_raw(config_file)
    return text, FileChange(config_file, before, text.replace("\n", newline), had_bom)


def _vcs_context(args, current_version, new_version):
    """Template context for the commit message, tag name and tag message."""
    context = {
        "current_version": args.current_version,
        "new_version": args.new_version,
    }
    context.update(time_context)
    context.update(prefixed_environ())
    context.update({'current_' + part: current_version[part].value for part in current_version})
    context.update({'new_' + part: new_version[part].value for part in new_version})
    context.update(special_char_context)
    return context


def _commit_to_vcs(files, context, config_file, config_file_exists, vcs, args,
                   current_version, new_version):
    commit_files = [f.path for f in files]
    if config_file_exists:
        commit_files.append(config_file)
    assert vcs.is_usable(), "Did find '{}' unusable, unable to commit.".format(
        vcs.__name__
    )
    do_commit = args.commit and not args.dry_run
    logger.info(
        "%s %s commit",
        "Would prepare" if not do_commit else "Preparing",
        vcs.__name__,
    )
    for path in commit_files:
        logger.info(
            "%s changes in file '%s' to %s",
            "Would add" if not do_commit else "Adding",
            path,
            vcs.__name__,
        )

        if do_commit:
            vcs.add_path(path)

    # Stage any extra files requested via --extra-files / extra_files config (#259)
    extra_files = getattr(args, "extra_files", None) or []
    for path in extra_files:
        logger.info(
            "%s extra file '%s' to %s",
            "Would add" if not do_commit else "Adding",
            path,
            vcs.__name__,
        )
        if do_commit:
            vcs.add_extra_path(path)

    context = _vcs_context(args, current_version, new_version)
    commit_message = args.message.format(**context)

    logger.info(
        "%s to %s with message '%s'",
        "Would commit" if not do_commit else "Committing",
        vcs.__name__,
        commit_message,
    )
    if do_commit:
        vcs.commit(
            message=commit_message,
            context=context,
            extra_args=[arg.strip() for arg in args.commit_args.splitlines()],
        )
    return context


def _tag_in_vcs(vcs, context, args):
    sign_tags = args.sign_tags
    tag_name = args.tag_name.format(**context)
    tag_message = args.tag_message.format(**context)
    do_tag = args.tag and not args.dry_run
    logger.info(
        "%s '%s' %s in %s and %s",
        "Would tag" if not do_tag else "Tagging",
        tag_name,
        "with message '{}'".format(tag_message) if tag_message else "without message",
        vcs.__name__,
        "signing" if sign_tags else "not signing",
    )
    if do_tag:
        vcs.tag(sign_tags, tag_name, tag_message)
