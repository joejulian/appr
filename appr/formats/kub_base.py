import io
import tempfile
import tarfile
import os.path

from requests.utils import urlparse

from appr.client import ApprClient
import appr.pack as packager


class KubBase(object):
    media_type = NotImplementedError
    target = NotImplementedError
    kub_class = NotImplementedError
    manifest_file = []
    appr_client = ApprClient

    def __init__(self, name, version='default', endpoint=None):
        self._deploy_name = name

        self.endpoint = endpoint
        self._registry = self.appr_client(endpoint=self.endpoint)
        self._deploy_version = version
        self._package = None
        self._manifest = None

    @property
    def package(self):
        if self._package is None:
            result = self._fetch_package()
            self._package = packager.ApprPackage(result, b64_encoded=False)
        return self._package

    def _create_manifest(self):
        raise NotImplementedError

    @property
    def manifest(self):
        if self._manifest is None:
            self._manifest = self._create_manifest()
        return self._manifest

    def __unicode__(self):
        return ("(<{class_name}({name}=={version})>".format(class_name=self.__class__.__name__,
                                                            name=self.name, version=self.version))

    def __str__(self):
        return self.__unicode__().encode('utf-8')

    def __repr__(self):
        return self.__str__()

    @property
    def author(self):
        pass

    @property
    def version(self):
        return self.manifest.version

    @property
    def description(self):
        pass

    @property
    def name(self):
        return self.manifest.name

    @property
    def variables(self):
        pass

    def _fetch_package(self):
        parse = urlparse(self._deploy_name)
        if parse.scheme in ["http", "https"]:
            # @TODO
            pass
        elif parse.scheme == "file":
            parts = parse.path.split("/")
            _, ext = os.path.splitext(parts[-1])
            if ext == ".gz":
                filepath = parse.path
            else:
                filepath = tempfile.NamedTemporaryFile().name
                packager.pack_kub(filepath)
            with open(filepath, "rb") as tarf:
                return tarf.read()
        else:
            return self._registry.pull(self._deploy_name, self._deploy_version, self.media_type)

    def make_tarfile(self, source_dir):
        output = io.BytesIO()
        with tarfile.open(fileobj=output, mode="w:gz") as tar:
            tar.add(source_dir, arcname=os.path.basename(source_dir))
        return output
