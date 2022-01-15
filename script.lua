function IncomingHttpRequestFilter(method, uri, ip, username, httpHeaders)
    -- Only allow GET requests for non-admin users (or 'uploader'-> used for pacs2go tools' direct upload)
    if method == 'GET' or string.find(uri,"/tools/find") ~= nil then -- extra: allow 'do lookup' in ORTHANC
        return true
    elseif username == 'admin' or username == 'uploader' then
        return true
    else
        print("no access")
        return false
    end
end

-- and string.find(uri, "/") ~= nil

function ReceivedInstanceFilter(dicom, origin, info)
    -- Only allow incoming MR images
    if dicom.PatientIdentityRemoved == 'YES' then
        print("Identity is removed")
        return true
    else
        print("You should remove the identity")
        return false
    end
end
