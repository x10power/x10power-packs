# pylint: disable=invalid-name
'''
Prepare Repository listing
'''
import os                     # for env vars
import re
import ssl
import urllib.request
import commentjson as json


def prepare_repository():
    '''
    open ../../meta/manifests/manifest.json for reading
    '''
    with open(
        os.path.join(
            "resources",
            "app",
            "meta",
            "manifests",
            "manifest.json"
        ),
        "r",
        encoding="utf-8") as repoManifestFile:
        repoManifestJSON = json.load(repoManifestFile)
        # open ../../repository.json for writing
        with open(
            os.path.join("repository.json"),
            "w",
            encoding="utf-8"
        ) as repoRepositoryFile:
            # write name from manifest to repository
            repoRepositoryJSON = {
                "name": repoManifestJSON["name"],
                "packages": []
            }
            with open(
                os.path.join("commit.txt"),
                "w",
                encoding="utf-8"
            ) as commit:
                commit.write("Updating Repository:" + "\n")
                commit.write("\n")
                for packManifestURL in repoManifestJSON["packages"]:
                    #  read each package from manifest
                    #   get package manifest from master branch
                    context = ssl._create_unverified_context()
                    with urllib.request.urlopen(
                        packManifestURL,
                        context=context
                    ) as packageReq:
                        packageJSON = json.loads(packageReq.read().decode("utf-8"))
                        toWrite = [
                            "Name: " + packageJSON["name"],
                            "By:   " + packageJSON["author"],
                            "URL:  " + packManifestURL
                        ]

                        #   get latest release from package
                        repoinfo = re.match(
                            r'http(?:s?)\:\/\/' + \
                            r'(?:[^\.]*)(?:\.?)(?:[^\.]*)(?:\.?)(?:[^\/]*)' + \
                            r'(?:\/)([^\/]*)(?:\/)([^\/]*)',
                            packManifestURL
                        )
                        user = repoinfo.group(1)
                        repo = repoinfo.group(2)
                        apiURL = f"https://api.github.com/repos/{user}/{repo}/releases/latest"
                        with urllib.request.urlopen(
                            apiURL,
                            context=context
                        ) as apiReq:
                            apiRes = json.loads(apiReq.read().decode("utf-8"))

                            #   get asset url
                            #   set link for package as asset url
                            packageJSON["link"] = apiRes["assets"][0]["browser_download_url"]
                            toWrite.append("ZIP:  " + packageJSON["link"])
                            toWrite.append("")

                            commit.write("\n".join(toWrite))

                            #   update other stuff
                            for key in ["uid", "version"]:
                                packageJSON[key] = packageJSON[f"package_{key}"]
                                del packageJSON[f"package_{key}"]

                            #   fix variants
                            curVariants = packageJSON["variants"]
                            newVariants = []
                            for [_, variant] in curVariants.items():
                                newVariant = {
                                    "name": variant["display_name"]
                                }
                                del variant["display_name"]
                                newVariant.update(variant)
                                newVariants.append(newVariant)
                            packageJSON["variants"] = newVariants

                            toWrite.append(f"Tag Name: {apiRes['tag_name']}")
                            # toWrite.append(
                            #     str(
                            #         re.match(
                            #             r'(?:[A-Za-z]*)([\d\.]*)',
                            #             apiRes["tag_name"]
                            #         )
                            #     )
                            # )

                            print("\n".join(toWrite))

                            packageJSON["version"] = re.match(
                                r'(?:[A-Za-z]*)([\d\.]*)',
                                apiRes["tag_name"]
                            ).group(1)
                            repoRepositoryJSON["packages"].append(packageJSON)

            repoRepositoryFile.seek(0)
            repoRepositoryFile.write(json.dumps(repoRepositoryJSON, indent=2))
            repoRepositoryFile.write("\n")
            repoRepositoryFile.truncate()


def main():
    '''
    Main
    '''
    prepare_repository()


if __name__ == "__main__":
    main()
else:
    raise AssertionError("Script improperly used as import!")
